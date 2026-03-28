"""End-to-end integration test: simulator audio → analysis → mapping → console output."""

import asyncio
import numpy as np
import pytest

from src.audio.analyzer import AudioAnalyzer
from src.audio.audio_bus import AudioBus
from src.audio.beat_detector import BeatDetector
from src.audio.simulator import AudioSimulator
from src.audio.types import AnalysisResult
from src.console.simulator import SimulatorConsole
from src.engine.events import AsyncEventBus
from src.engine.loop import EngineLoop
from src.engine.state import AppState
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry
from src.mapping.types import MappingRule


@pytest.mark.asyncio
class TestFullPipelineIntegration:
    """Tests the complete audio → analysis → mapping → output pipeline."""

    async def test_simulator_to_mapping_output(self):
        """Synthetic kick pattern audio should drive a fader via a mapping rule."""
        # --- Setup components ---
        simulator = AudioSimulator(mode="kick_pattern", bpm=120, buffer_size=1024)
        analyzer = AudioAnalyzer(sample_rate=48000, buffer_size=1024)
        beat_detector = BeatDetector(sample_rate=48000, buffer_size=1024)
        audio_bus = AudioBus()
        audio_bus.set_loop(asyncio.get_running_loop())

        console = SimulatorConsole(num_playbacks=5)
        registry = ParameterRegistry()
        registry.register_console(console)
        mapping_engine = MappingEngine(registry=registry)

        state = AppState()
        state.active_console = console.name
        event_bus = AsyncEventBus()

        # Add rule: audio.band.sub → playback.1.fader (with smooth)
        rule = MappingRule(
            id="integration-test-rule",
            name="Sub Bass to Fader",
            input_param="audio.band.sub",
            output_param="simulator.playback.1.fader",
            transform_chain=[
                {"type": "Smooth", "attack": 0.05, "release": 0.1},
            ],
            enabled=True,
        )
        mapping_engine.add_rule(rule)

        engine = EngineLoop(
            audio_bus=audio_bus,
            mapping_engine=mapping_engine,
            console=console,
            adapters=[],
            state=state,
            event_bus=event_bus,
        )

        # --- Start the simulator and process some frames manually ---
        simulator.start()

        # Let the simulator produce some audio
        await asyncio.sleep(0.2)

        # Process frames through the analysis pipeline
        non_zero_outputs = 0
        for _ in range(20):
            frame_data = simulator.ring_buffer.read()
            if frame_data is not None:
                analysis = analyzer.analyze(frame_data)
                onset, beat, bpm, phase = beat_detector.process(analysis.spectral_flux)
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
                audio_bus.publish(result)

                # Evaluate mappings
                outputs = mapping_engine.evaluate(result, dt=0.025)
                if outputs and outputs[0].value > 0.01:
                    non_zero_outputs += 1

            await asyncio.sleep(0.02)

        simulator.stop()

        # The kick pattern should have produced some non-zero sub-bass energy
        assert non_zero_outputs > 0, "Expected mapping to produce non-zero output from kick pattern"

    async def test_engine_loop_with_simulator(self):
        """Full engine loop running with audio simulator for a brief period."""
        simulator = AudioSimulator(mode="kick_pattern", bpm=120, buffer_size=1024)
        analyzer = AudioAnalyzer(sample_rate=48000, buffer_size=1024)
        beat_detector = BeatDetector(sample_rate=48000, buffer_size=1024)
        audio_bus = AudioBus()
        audio_bus.set_loop(asyncio.get_running_loop())

        console = SimulatorConsole(num_playbacks=5)
        registry = ParameterRegistry()
        registry.register_console(console)
        mapping_engine = MappingEngine(registry=registry)

        state = AppState()
        event_bus = AsyncEventBus()

        # Simple RMS mapping
        rule = MappingRule(
            id="rms-rule",
            name="RMS to Fader",
            input_param="audio.rms",
            output_param="simulator.playback.1.fader",
            transform_chain=[],
            enabled=True,
        )
        mapping_engine.add_rule(rule)

        engine = EngineLoop(
            audio_bus=audio_bus,
            mapping_engine=mapping_engine,
            console=console,
            adapters=[],
            state=state,
            event_bus=event_bus,
        )

        # Start simulator and feed frames into the bus
        simulator.start()

        async def feed_audio():
            """Poll simulator and publish analysis results."""
            while True:
                frame_data = simulator.ring_buffer.read()
                if frame_data is not None:
                    analysis = analyzer.analyze(frame_data)
                    onset, beat, bpm, phase = beat_detector.process(analysis.spectral_flux)
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
                    audio_bus.publish(result)
                await asyncio.sleep(0.01)

        feed_task = asyncio.create_task(feed_audio())

        await engine.start()
        await asyncio.sleep(0.5)
        await engine.stop()

        feed_task.cancel()
        try:
            await feed_task
        except asyncio.CancelledError:
            pass

        simulator.stop()

        # Verify the engine ran and produced results
        assert state.tick_count > 5
        assert state.fps > 0
        assert len(state.latest_outputs) > 0

    async def test_snapshot_serializable(self):
        """Verify the state snapshot is JSON-serializable after running the pipeline."""
        import json

        audio_bus = AudioBus()
        audio_bus.set_loop(asyncio.get_running_loop())

        console = SimulatorConsole(num_playbacks=3)
        registry = ParameterRegistry()
        registry.register_console(console)
        mapping_engine = MappingEngine(registry=registry)

        state = AppState()
        state.active_console = console.name
        event_bus = AsyncEventBus()

        engine = EngineLoop(
            audio_bus=audio_bus,
            mapping_engine=mapping_engine,
            console=console,
            adapters=[],
            state=state,
            event_bus=event_bus,
        )

        await engine.start()
        await asyncio.sleep(0.1)
        await engine.stop()

        snapshot = state.to_snapshot()
        # Should not raise
        json_str = json.dumps(snapshot)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert "audio" in parsed
        assert "engine" in parsed

    async def test_multiple_mapping_rules(self):
        """Multiple mapping rules should all evaluate independently."""
        audio_bus = AudioBus()
        audio_bus.set_loop(asyncio.get_running_loop())

        console = SimulatorConsole(num_playbacks=5)
        registry = ParameterRegistry()
        registry.register_console(console)
        mapping_engine = MappingEngine(registry=registry)

        state = AppState()
        event_bus = AsyncEventBus()

        # Two rules targeting different outputs
        mapping_engine.add_rule(MappingRule(
            id="rule-1", name="RMS Fader 1",
            input_param="audio.rms",
            output_param="simulator.playback.1.fader",
        ))
        mapping_engine.add_rule(MappingRule(
            id="rule-2", name="Peak Fader 2",
            input_param="audio.peak",
            output_param="simulator.playback.2.fader",
        ))

        # Provide analysis with known values
        analysis = AnalysisResult(rms=0.5, peak=0.8)
        audio_bus._latest = analysis

        engine = EngineLoop(
            audio_bus=audio_bus,
            mapping_engine=mapping_engine,
            console=console,
            adapters=[],
            state=state,
            event_bus=event_bus,
        )

        await engine.start()
        await asyncio.sleep(0.15)
        await engine.stop()

        assert len(state.latest_outputs) == 2
        targets = {o.target: o.value for o in state.latest_outputs}
        assert targets["simulator.playback.1.fader"] == pytest.approx(0.5, abs=0.01)
        assert targets["simulator.playback.2.fader"] == pytest.approx(0.8, abs=0.01)
