"""Tests for the parameter registry and input resolution."""

import pytest

from src.audio.types import AnalysisResult, BandEnergies
from src.console.simulator import SimulatorConsole
from src.mapping.parameters import ParameterRegistry


class TestParameterRegistry:
    def test_default_audio_inputs_registered(self):
        reg = ParameterRegistry()
        inputs = reg.inputs
        assert "audio.rms" in inputs
        assert "audio.peak" in inputs
        assert "audio.band.sub" in inputs
        assert "audio.band.low" in inputs
        assert "audio.band.mid" in inputs
        assert "audio.band.hi_mid" in inputs
        assert "audio.band.high" in inputs
        assert "audio.bpm" in inputs
        assert "audio.beat" in inputs
        assert "audio.onset" in inputs
        assert "audio.beat_phase" in inputs
        assert "audio.spectral_centroid" in inputs
        assert "audio.spectral_flux" in inputs

    def test_no_outputs_initially(self):
        reg = ParameterRegistry()
        assert len(reg.outputs) == 0

    def test_register_console_populates_outputs(self):
        reg = ParameterRegistry()
        sim = SimulatorConsole(num_playbacks=3)
        reg.register_console(sim)
        outputs = reg.outputs
        assert len(outputs) == 9  # 3 * 3
        assert "simulator.playback.1.fader" in outputs

    def test_has_input(self):
        reg = ParameterRegistry()
        assert reg.has_input("audio.rms") is True
        assert reg.has_input("nonexistent") is False

    def test_has_output(self):
        reg = ParameterRegistry()
        sim = SimulatorConsole(num_playbacks=1)
        reg.register_console(sim)
        assert reg.has_output("simulator.playback.1.fader") is True
        assert reg.has_output("nonexistent") is False


class TestResolveInput:
    def test_resolve_rms(self):
        result = AnalysisResult(rms=0.75)
        assert ParameterRegistry.resolve_input("audio.rms", result) == 0.75

    def test_resolve_peak(self):
        result = AnalysisResult(peak=0.9)
        assert ParameterRegistry.resolve_input("audio.peak", result) == 0.9

    def test_resolve_band_sub(self):
        result = AnalysisResult(band_energies=BandEnergies(sub=0.8))
        assert ParameterRegistry.resolve_input("audio.band.sub", result) == 0.8

    def test_resolve_band_hi_mid(self):
        result = AnalysisResult(band_energies=BandEnergies(hi_mid=0.3))
        assert ParameterRegistry.resolve_input("audio.band.hi_mid", result) == 0.3

    def test_resolve_bpm_normalized(self):
        result = AnalysisResult(bpm=120.0)
        assert ParameterRegistry.resolve_input("audio.bpm", result) == pytest.approx(0.6)

    def test_resolve_beat_true(self):
        result = AnalysisResult(beat_detected=True)
        assert ParameterRegistry.resolve_input("audio.beat", result) == 1.0

    def test_resolve_beat_false(self):
        result = AnalysisResult(beat_detected=False)
        assert ParameterRegistry.resolve_input("audio.beat", result) == 0.0

    def test_resolve_onset(self):
        result = AnalysisResult(onset_detected=True)
        assert ParameterRegistry.resolve_input("audio.onset", result) == 1.0

    def test_resolve_beat_phase(self):
        result = AnalysisResult(beat_phase=0.5)
        assert ParameterRegistry.resolve_input("audio.beat_phase", result) == 0.5

    def test_resolve_spectral_centroid(self):
        result = AnalysisResult(spectral_centroid=0.4)
        assert ParameterRegistry.resolve_input("audio.spectral_centroid", result) == 0.4

    def test_resolve_spectral_flux(self):
        result = AnalysisResult(spectral_flux=0.7)
        assert ParameterRegistry.resolve_input("audio.spectral_flux", result) == 0.7

    def test_resolve_unknown_returns_zero(self):
        result = AnalysisResult()
        assert ParameterRegistry.resolve_input("audio.nonexistent", result) == 0.0
        assert ParameterRegistry.resolve_input("something.else", result) == 0.0
        assert ParameterRegistry.resolve_input("", result) == 0.0

    def test_resolve_unknown_band_returns_zero(self):
        result = AnalysisResult()
        assert ParameterRegistry.resolve_input("audio.band.nonexistent", result) == 0.0
