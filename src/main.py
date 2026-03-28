"""LuxForge — Audio-reactive lighting control system.

Application entry point. Wires up audio capture/simulator, analysis,
mapping engine, console interface, protocol adapters, and the engine loop.
"""

import argparse
import asyncio

import structlog
import uvicorn

from src.config import AppConfig
from src.api import dependencies as deps
from src.api.app import create_app
from src.audio.analyzer import AudioAnalyzer
from src.audio.audio_bus import AudioBus
from src.audio.beat_detector import BeatDetector
from src.audio.types import AnalysisResult
from src.console.simulator import SimulatorConsole
from src.engine.events import AsyncEventBus
from src.engine.loop import EngineLoop
from src.engine.state import AppState
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry
from src.protocols.base import ProtocolAdapter
from src.protocols.osc_adapter import OSCAdapter
from src.fixtures.library import FixtureLibrary
from src.fixtures.patch import PatchManager
from src.scenes.manager import SceneManager
from src.scenes.storage import SceneStorage

logger = structlog.get_logger()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LuxForge — Audio-reactive lighting control")
    parser.add_argument(
        "--simulator", action="store_true", default=False,
        help="Force simulator mode (no hardware required)",
    )
    parser.add_argument(
        "--config", type=str, default=None,
        help="Path to a .env config file",
    )
    return parser.parse_args()


def build_audio_source(config: AppConfig, use_simulator: bool):
    """Create either AudioSimulator or AudioCapture based on config."""
    if use_simulator or config.simulator.enabled or config.audio.device_index is None:
        from src.audio.simulator import AudioSimulator
        return AudioSimulator(
            mode=config.simulator.mode,
            sample_rate=config.audio.sample_rate,
            buffer_size=config.audio.buffer_size,
            bpm=config.simulator.bpm,
            frequency=config.simulator.frequency,
        )
    else:
        from src.audio.capture import AudioCapture
        return AudioCapture(
            device_index=config.audio.device_index,
            sample_rate=config.audio.sample_rate,
            buffer_size=config.audio.buffer_size,
        )


def build_console(config: AppConfig, use_simulator: bool):
    """Create either SimulatorConsole or OnyxConsole."""
    if use_simulator or config.simulator.enabled:
        return SimulatorConsole(num_playbacks=10)
    else:
        from src.console.onyx import OnyxConsole
        return OnyxConsole()


def build_adapters(config: AppConfig, use_simulator: bool) -> list[ProtocolAdapter]:
    """Create protocol adapters, forcing dry_run in simulator mode."""
    adapters: list[ProtocolAdapter] = []

    force_dry = use_simulator or config.simulator.enabled
    adapters.append(OSCAdapter(
        host=config.osc.host,
        port=config.osc.port,
        dry_run=force_dry or config.osc.dry_run,
    ))

    # MIDI adapter (optional — only if port configured or in dry_run)
    try:
        from src.protocols.midi_adapter import MIDIAdapter
        adapters.append(MIDIAdapter(
            port_name=config.midi.port_name,
            dry_run=force_dry or config.midi.dry_run,
        ))
    except ImportError:
        logger.debug("midi_adapter_not_available")

    # Art-Net adapter
    try:
        from src.protocols.artnet_adapter import ArtNetAdapter
        adapters.append(ArtNetAdapter(
            host=config.artnet.host,
            port=config.artnet.port,
            universe=config.artnet.universe,
            dry_run=force_dry or config.artnet.dry_run,
        ))
    except ImportError:
        logger.debug("artnet_adapter_not_available")

    # sACN adapter
    try:
        from src.protocols.sacn_adapter import SACNAdapter
        adapters.append(SACNAdapter(
            universe=config.sacn.universe,
            multicast=config.sacn.multicast,
            unicast_dest=config.sacn.unicast_dest,
            dry_run=force_dry or config.sacn.dry_run,
        ))
    except ImportError:
        logger.debug("sacn_adapter_not_available")

    return adapters


class AudioProcessingBridge:
    """Reads frames from the audio source, runs analysis + beat detection,
    and publishes results to the AudioBus. Runs as an asyncio task."""

    def __init__(
        self,
        audio_source,
        analyzer: AudioAnalyzer,
        beat_detector: BeatDetector,
        audio_bus: AudioBus,
    ) -> None:
        self._source = audio_source
        self._analyzer = analyzer
        self._beat_detector = beat_detector
        self._bus = audio_bus
        self._running = False
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        """Poll the ring buffer and process frames."""
        while self._running:
            frame_data = self._source.ring_buffer.read()
            if frame_data is not None:
                # Run FFT analysis
                analysis = self._analyzer.analyze(frame_data)

                # Run beat detection on spectral flux
                onset, beat, bpm, phase = self._beat_detector.process(analysis.spectral_flux)

                # Merge beat data into the analysis result
                result = AnalysisResult(
                    fft_magnitudes=analysis.fft_magnitudes,
                    band_energies=analysis.band_energies,
                    spectral_centroid=analysis.spectral_centroid,
                    spectral_flux=analysis.spectral_flux,
                    rms=analysis.rms,
                    peak=analysis.peak,
                    beat_detected=beat,
                    bpm=bpm,
                    beat_phase=phase,
                    onset_detected=onset,
                )
                self._bus.publish(result)
                await asyncio.sleep(0)  # Yield to event loop
            else:
                # No data yet — wait a short interval
                await asyncio.sleep(0.005)


async def run_app(args: argparse.Namespace) -> None:
    """Main async application lifecycle."""
    config = AppConfig()
    use_simulator = args.simulator or config.simulator.enabled

    mode_label = "SIMULATOR" if use_simulator else "HARDWARE"
    logger.info("luxforge_starting", mode=mode_label)

    # --- Build components ---
    audio_source = build_audio_source(config, use_simulator)
    console = build_console(config, use_simulator)
    adapters = build_adapters(config, use_simulator)

    analyzer = AudioAnalyzer(
        sample_rate=config.audio.sample_rate,
        buffer_size=config.audio.buffer_size,
    )
    beat_detector = BeatDetector(
        sample_rate=config.audio.sample_rate,
        buffer_size=config.audio.buffer_size,
    )

    audio_bus = AudioBus()
    audio_bus.set_loop(asyncio.get_running_loop())

    event_bus = AsyncEventBus()
    state = AppState()
    state.active_console = console.name

    param_registry = ParameterRegistry()
    param_registry.register_console(console)

    mapping_engine = MappingEngine(registry=param_registry)

    # --- Wire up API dependencies ---
    deps.state = state
    deps.event_bus = event_bus
    deps.mapping_engine = mapping_engine
    deps.param_registry = param_registry
    deps.console = console
    deps.adapters = adapters
    deps.audio_source = audio_source
    deps.config = config

    # --- Scene manager ---
    scene_storage = SceneStorage(db_path="luxforge.db")
    scene_manager = SceneManager(
        storage=scene_storage,
        mapping_engine=mapping_engine,
        console=console,
        adapters=adapters,
        event_bus=event_bus,
    )
    await scene_manager.init()
    deps.scene_manager = scene_manager

    # --- Fixture library + patch manager ---
    fixture_library = FixtureLibrary()
    fixture_library.load_profiles()
    patch_manager = PatchManager(library=fixture_library)
    deps.fixture_library = fixture_library
    deps.patch_manager = patch_manager

    engine_loop = EngineLoop(
        audio_bus=audio_bus,
        mapping_engine=mapping_engine,
        console=console,
        adapters=adapters,
        state=state,
        event_bus=event_bus,
    )

    bridge = AudioProcessingBridge(audio_source, analyzer, beat_detector, audio_bus)

    # --- Connect adapters ---
    for adapter in adapters:
        try:
            await adapter.connect()
            logger.info("adapter_connected", adapter=adapter.name, dry_run=adapter.dry_run)
        except Exception:
            logger.exception("adapter_connect_failed", adapter=adapter.name)

    # --- Start audio ---
    audio_source.start()
    logger.info("audio_source_started", type=type(audio_source).__name__)

    # --- Start engine ---
    await bridge.start()
    await engine_loop.start()

    logger.info(
        "luxforge_running",
        mode=mode_label,
        console=console.name,
        adapters=[a.name for a in adapters],
        api_port=config.api.port,
    )

    # --- Start FastAPI server ---
    app = create_app()
    server_config = uvicorn.Config(
        app,
        host=config.api.host,
        port=config.api.port,
        log_level="info",
    )
    server = uvicorn.Server(server_config)

    # Run uvicorn — it handles SIGINT/SIGTERM internally
    try:
        await server.serve()
    finally:
        # --- Graceful shutdown ---
        logger.info("luxforge_shutting_down")

        await engine_loop.stop()
        await bridge.stop()
        audio_source.stop()
        await scene_manager.close()

        for adapter in adapters:
            try:
                await adapter.disconnect()
            except Exception:
                logger.exception("adapter_disconnect_failed", adapter=adapter.name)

        logger.info("luxforge_stopped")


def main() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    args = parse_args()

    try:
        asyncio.run(run_app(args))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
