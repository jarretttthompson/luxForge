"""Tests for the EngineLoop."""

import asyncio
import numpy as np
import pytest

from src.audio.audio_bus import AudioBus
from src.audio.types import AnalysisResult, BandEnergies
from src.console.simulator import SimulatorConsole
from src.engine.events import AsyncEventBus
from src.engine.loop import EngineLoop
from src.engine.state import AppState
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry
from src.mapping.types import MappingRule


@pytest.mark.asyncio
class TestEngineLoop:
    def _make_loop(self):
        audio_bus = AudioBus()
        audio_bus.set_loop(asyncio.get_running_loop())

        console = SimulatorConsole(num_playbacks=3)
        registry = ParameterRegistry()
        registry.register_console(console)
        mapping_engine = MappingEngine(registry=registry)

        state = AppState()
        event_bus = AsyncEventBus()

        engine = EngineLoop(
            audio_bus=audio_bus,
            mapping_engine=mapping_engine,
            console=console,
            adapters=[],
            state=state,
            event_bus=event_bus,
        )
        return engine, audio_bus, state, event_bus, mapping_engine

    async def test_start_stop(self):
        engine, _, state, _, _ = self._make_loop()

        await engine.start()
        assert engine.running is True
        assert state.engine_running is True

        await asyncio.sleep(0.1)
        assert state.tick_count > 0

        await engine.stop()
        assert engine.running is False
        assert state.engine_running is False

    async def test_processes_audio_data(self):
        engine, audio_bus, state, _, _ = self._make_loop()

        # Publish an analysis result
        analysis = AnalysisResult(
            rms=0.6,
            peak=0.9,
            band_energies=BandEnergies(sub=0.8),
        )
        audio_bus._latest = analysis

        await engine.start()
        await asyncio.sleep(0.15)
        await engine.stop()

        assert state.analysis.rms == 0.6
        assert state.tick_count > 0

    async def test_evaluates_mapping_rules(self):
        engine, audio_bus, state, _, mapping_engine = self._make_loop()

        # Add a mapping rule: audio.rms -> simulator.playback.1.fader
        rule = MappingRule(
            id="test-rule",
            name="Test Rule",
            input_param="audio.rms",
            output_param="simulator.playback.1.fader",
            transform_chain=[],
            enabled=True,
        )
        mapping_engine.add_rule(rule)

        # Provide audio data
        analysis = AnalysisResult(rms=0.75)
        audio_bus._latest = analysis

        await engine.start()
        await asyncio.sleep(0.15)
        await engine.stop()

        # Should have output values
        assert len(state.latest_outputs) > 0
        assert state.latest_outputs[0].target == "simulator.playback.1.fader"
        assert state.latest_outputs[0].value == pytest.approx(0.75, abs=0.01)

    async def test_publishes_events(self):
        engine, audio_bus, state, event_bus, _ = self._make_loop()

        events_received = []

        async def on_started(data=None):
            events_received.append("started")

        async def on_stopped(data=None):
            events_received.append("stopped")

        async def on_output(data):
            events_received.append("output")

        event_bus.subscribe("engine.started", on_started)
        event_bus.subscribe("engine.stopped", on_stopped)
        event_bus.subscribe("mapping.output", on_output)

        await engine.start()
        await asyncio.sleep(0.1)
        await engine.stop()

        assert "started" in events_received
        assert "stopped" in events_received

    async def test_fps_tracking(self):
        engine, _, state, _, _ = self._make_loop()

        await engine.start()
        await asyncio.sleep(0.3)
        await engine.stop()

        # FPS should be roughly near 40
        assert state.fps > 10  # At least some reasonable rate

    async def test_double_start_is_safe(self):
        engine, _, _, _, _ = self._make_loop()
        await engine.start()
        await engine.start()  # Should not raise
        await engine.stop()

    async def test_stop_when_not_running(self):
        engine, _, _, _, _ = self._make_loop()
        await engine.stop()  # Should not raise
