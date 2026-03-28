"""Main engine loop: orchestrates audio analysis → mapping → protocol output at 40Hz."""

import asyncio
import time

import structlog

from src.audio.audio_bus import AudioBus
from src.audio.types import AnalysisResult
from src.console.base import ConsoleInterface
from src.console.types import ConsoleCommand, ConsoleCapability
from src.engine.events import AsyncEventBus
from src.engine.state import AppState, ProtocolStatus
from src.mapping.engine import MappingEngine
from src.mapping.types import OutputValue
from src.protocols.base import ProtocolAdapter

logger = structlog.get_logger()

TARGET_HZ = 40
TICK_INTERVAL = 1.0 / TARGET_HZ


class EngineLoop:
    """Runs at 40Hz, reading audio analysis and driving lighting output.

    Each tick:
    1. Read latest AnalysisResult from AudioBus
    2. Evaluate mapping rules via MappingEngine
    3. Translate OutputValues through ConsoleInterface → ProtocolMessages
    4. Send through protocol adapters
    5. Update AppState
    6. Publish events for WebSocket broadcast
    """

    def __init__(
        self,
        audio_bus: AudioBus,
        mapping_engine: MappingEngine,
        console: ConsoleInterface,
        adapters: list[ProtocolAdapter],
        state: AppState,
        event_bus: AsyncEventBus,
    ) -> None:
        self._audio_bus = audio_bus
        self._mapping_engine = mapping_engine
        self._console = console
        self._adapters = adapters
        self._state = state
        self._event_bus = event_bus
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_tick_time: float = 0.0

    @property
    def running(self) -> bool:
        return self._running

    async def start(self) -> None:
        """Start the engine loop as an asyncio task."""
        if self._running:
            logger.warning("engine_already_running")
            return

        self._running = True
        self._state.engine_running = True
        self._last_tick_time = time.monotonic()
        self._task = asyncio.create_task(self._run())
        logger.info("engine_started", target_hz=TARGET_HZ)
        await self._event_bus.publish("engine.started")

    async def stop(self) -> None:
        """Stop the engine loop gracefully."""
        if not self._running:
            return

        self._running = False
        self._state.engine_running = False

        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

        logger.info("engine_stopped", tick_count=self._state.tick_count)
        await self._event_bus.publish("engine.stopped")

    async def _run(self) -> None:
        """Main loop running at ~40Hz."""
        fps_window: list[float] = []

        while self._running:
            tick_start = time.monotonic()
            dt = tick_start - self._last_tick_time
            self._last_tick_time = tick_start

            try:
                await self._tick(dt)
            except Exception:
                logger.exception("engine_tick_error")

            # Track FPS
            fps_window.append(dt)
            if len(fps_window) > TARGET_HZ:
                fps_window.pop(0)
            avg_dt = sum(fps_window) / len(fps_window)
            self._state.fps = 1.0 / avg_dt if avg_dt > 0 else 0.0

            # Sleep to maintain target rate
            elapsed = time.monotonic() - tick_start
            sleep_time = TICK_INTERVAL - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def _tick(self, dt: float) -> None:
        """Execute one engine tick."""
        # 1. Read latest analysis from the audio bus
        analysis = self._audio_bus.latest
        if analysis is None:
            analysis = AnalysisResult()

        # 2. Update state with current analysis
        await self._state.update_analysis(analysis)

        # 3. Evaluate mapping rules
        outputs = self._mapping_engine.evaluate(analysis, dt)

        # 4. Translate outputs to console commands and protocol messages
        for output in outputs:
            command = self._resolve_command(output)
            output.console_command = command

            if command is not None:
                messages = self._console.translate(command)
                for msg in messages:
                    self._send_to_adapters(msg)

        # 5. Update state with outputs
        await self._state.update_outputs(outputs)
        self._state.tick_count += 1

        # 6. Update protocol statuses
        for adapter in self._adapters:
            self._state.protocol_statuses[adapter.name] = ProtocolStatus(
                name=adapter.name,
                connected=adapter.is_connected(),
                dry_run=adapter.dry_run,
            )

        # 7. Publish event for WebSocket broadcast
        await self._event_bus.publish("mapping.output", outputs)

    def _resolve_command(self, output: OutputValue) -> ConsoleCommand | None:
        """Convert an OutputValue into a ConsoleCommand based on the target name."""
        target = output.target
        if not target:
            return None

        # Determine command type from the target name
        if target.endswith(".fader"):
            cmd_type = ConsoleCapability.PLAYBACK_FADER
        elif target.endswith(".go"):
            cmd_type = ConsoleCapability.PLAYBACK_GO
        elif target.endswith(".stop"):
            cmd_type = ConsoleCapability.PLAYBACK_STOP
        else:
            cmd_type = ConsoleCapability.PLAYBACK_FADER

        return ConsoleCommand(
            target=target,
            value=output.value,
            command_type=cmd_type,
        )

    def _send_to_adapters(self, message) -> None:
        """Send a protocol message to all connected adapters that can handle it."""
        from src.protocols.types import OSCMessage, MIDIMessage, DMXFrame

        for adapter in self._adapters:
            try:
                # Route message to appropriate adapter based on type
                if isinstance(message, OSCMessage) and "osc" in adapter.name.lower():
                    adapter.send(message)
                elif isinstance(message, MIDIMessage) and "midi" in adapter.name.lower():
                    adapter.send(message)
                elif isinstance(message, DMXFrame) and (
                    "artnet" in adapter.name.lower() or "sacn" in adapter.name.lower()
                ):
                    adapter.send(message)
            except Exception:
                logger.exception(
                    "adapter_send_error",
                    adapter=adapter.name,
                    message_type=type(message).__name__,
                )
