"""Tests for AppState."""

import asyncio
import numpy as np
import pytest

from src.audio.types import AnalysisResult, BandEnergies
from src.engine.state import AppState, ProtocolStatus


@pytest.mark.asyncio
class TestAppState:
    async def test_initial_state(self):
        state = AppState()
        assert state.engine_running is False
        assert state.tick_count == 0
        assert state.active_console == "none"
        assert state.latest_outputs == []

    async def test_update_analysis(self):
        state = AppState()
        analysis = AnalysisResult(rms=0.5, peak=0.8)
        await state.update_analysis(analysis)
        assert state.analysis.rms == 0.5
        assert state.analysis.peak == 0.8

    async def test_update_outputs(self):
        from src.mapping.types import OutputValue
        state = AppState()
        outputs = [OutputValue(target="test.fader", value=0.75)]
        await state.update_outputs(outputs)
        assert len(state.latest_outputs) == 1
        assert state.latest_outputs[0].value == 0.75

    async def test_to_snapshot_structure(self):
        state = AppState()
        state.engine_running = True
        state.fps = 39.5
        state.tick_count = 100
        state.active_console = "simulator"
        state.protocol_statuses["osc"] = ProtocolStatus(
            name="osc", connected=True, dry_run=True
        )

        snap = state.to_snapshot()

        assert "audio" in snap
        assert "outputs" in snap
        assert "engine" in snap
        assert snap["engine"]["running"] is True
        assert snap["engine"]["fps"] == 39.5
        assert snap["console"] == "simulator"
        assert "osc" in snap["protocols"]
        assert snap["protocols"]["osc"]["dry_run"] is True

    async def test_to_snapshot_fft_downsampling(self):
        state = AppState()
        # Create analysis with a large FFT array
        fft = np.random.rand(513).astype(np.float32)
        state.analysis = AnalysisResult(fft_magnitudes=fft)

        snap = state.to_snapshot()
        assert len(snap["audio"]["fft"]) == 64

    async def test_to_snapshot_small_fft(self):
        state = AppState()
        fft = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        state.analysis = AnalysisResult(fft_magnitudes=fft)

        snap = state.to_snapshot()
        assert len(snap["audio"]["fft"]) == 3
