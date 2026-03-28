"""Tests for audio analyzer: FFT, band energy, RMS, spectral features."""

import time
import numpy as np
import pytest

from src.audio.analyzer import AudioAnalyzer, BandRange


SAMPLE_RATE = 48000
BUFFER_SIZE = 1024


def make_sine(frequency: float, sample_rate: int = SAMPLE_RATE,
              buffer_size: int = BUFFER_SIZE, amplitude: float = 1.0) -> np.ndarray:
    """Generate a sine wave at the given frequency."""
    t = np.arange(buffer_size, dtype=np.float32) / sample_rate
    return (np.sin(2 * np.pi * frequency * t) * amplitude).astype(np.float32)


def make_silence(buffer_size: int = BUFFER_SIZE) -> np.ndarray:
    return np.zeros(buffer_size, dtype=np.float32)


class TestAnalyzerBasics:
    def test_returns_analysis_result(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result = analyzer.analyze(make_sine(440.0))
        assert result.fft_magnitudes is not None
        assert len(result.fft_magnitudes) == BUFFER_SIZE // 2 + 1

    def test_rms_of_silence_is_zero(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result = analyzer.analyze(make_silence())
        assert result.rms == pytest.approx(0.0, abs=1e-6)

    def test_peak_of_silence_is_zero(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result = analyzer.analyze(make_silence())
        assert result.peak == pytest.approx(0.0, abs=1e-6)

    def test_rms_of_full_scale_sine(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        # Feed a few frames so normalization adapts
        sine = make_sine(440.0, amplitude=1.0)
        for _ in range(5):
            result = analyzer.analyze(sine)
        # RMS of a full-scale sine is ~0.707, but we're testing normalized value
        # After adaptation, it should be close to 1.0 (it's the max signal)
        assert result.rms > 0.5

    def test_peak_of_full_scale_sine(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result = analyzer.analyze(make_sine(440.0, amplitude=1.0))
        assert result.peak == pytest.approx(1.0, abs=0.01)

    def test_all_values_in_range(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        # Run several frames
        for freq in [100, 440, 1000, 5000, 10000]:
            result = analyzer.analyze(make_sine(float(freq)))
            assert 0.0 <= result.rms <= 1.0
            assert 0.0 <= result.peak <= 1.0
            assert 0.0 <= result.spectral_centroid <= 1.0
            assert 0.0 <= result.spectral_flux <= 1.0
            assert 0.0 <= result.band_energies.sub <= 1.0
            assert 0.0 <= result.band_energies.low <= 1.0
            assert 0.0 <= result.band_energies.mid <= 1.0
            assert 0.0 <= result.band_energies.hi_mid <= 1.0
            assert 0.0 <= result.band_energies.high <= 1.0


class TestBandEnergies:
    def test_low_frequency_lights_up_sub_and_low(self):
        """A 40 Hz sine should have energy in the sub band."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine_40hz = make_sine(40.0)
        # Run a few frames for normalization to settle
        for _ in range(10):
            result = analyzer.analyze(sine_40hz)
        assert result.band_energies.sub > 0.3, f"Sub band energy too low: {result.band_energies.sub}"

    def test_100hz_lights_up_low_band(self):
        """A 100 Hz sine should have energy in the low band."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine_100hz = make_sine(100.0)
        for _ in range(10):
            result = analyzer.analyze(sine_100hz)
        assert result.band_energies.low > 0.3, f"Low band energy too low: {result.band_energies.low}"

    def test_1khz_lights_up_mid_band(self):
        """A 1 kHz sine should have energy in the mid band."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine_1khz = make_sine(1000.0)
        for _ in range(10):
            result = analyzer.analyze(sine_1khz)
        assert result.band_energies.mid > 0.3, f"Mid band energy too low: {result.band_energies.mid}"

    def test_4khz_lights_up_hi_mid_band(self):
        """A 4 kHz sine should have energy in the hi_mid band."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine_4khz = make_sine(4000.0)
        for _ in range(10):
            result = analyzer.analyze(sine_4khz)
        assert result.band_energies.hi_mid > 0.3, f"Hi-mid band energy too low: {result.band_energies.hi_mid}"

    def test_10khz_lights_up_high_band(self):
        """A 10 kHz sine should have energy in the high band."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine_10khz = make_sine(10000.0)
        for _ in range(10):
            result = analyzer.analyze(sine_10khz)
        assert result.band_energies.high > 0.3, f"High band energy too low: {result.band_energies.high}"

    def test_low_freq_does_not_light_high_band(self):
        """A 100 Hz sine should NOT have significant energy in the high band."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine_100hz = make_sine(100.0)
        for _ in range(10):
            result = analyzer.analyze(sine_100hz)
        # High band should be very low for a 100 Hz signal
        assert result.band_energies.high < 0.1, f"High band should be low for 100Hz: {result.band_energies.high}"


class TestSpectralFeatures:
    def test_spectral_flux_zero_on_first_frame(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result = analyzer.analyze(make_sine(440.0))
        assert result.spectral_flux == pytest.approx(0.0, abs=1e-6)

    def test_spectral_flux_nonzero_on_change(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        # First frame: silence
        analyzer.analyze(make_silence())
        # Second frame: loud sine — big spectral change
        result = analyzer.analyze(make_sine(440.0, amplitude=1.0))
        assert result.spectral_flux > 0.0

    def test_spectral_flux_low_on_steady_signal(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        sine = make_sine(440.0)
        # Feed several identical frames
        for _ in range(20):
            result = analyzer.analyze(sine)
        # Flux should be very low for a steady signal
        assert result.spectral_flux < 0.1

    def test_spectral_centroid_higher_for_high_freq(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result_low = analyzer.analyze(make_sine(200.0))
        analyzer.reset()
        result_high = analyzer.analyze(make_sine(8000.0))
        assert result_high.spectral_centroid > result_low.spectral_centroid

    def test_spectral_centroid_in_range(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        result = analyzer.analyze(make_sine(440.0))
        assert 0.0 <= result.spectral_centroid <= 1.0


class TestReset:
    def test_reset_clears_state(self):
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        # Build up some state
        for _ in range(10):
            analyzer.analyze(make_sine(440.0))
        analyzer.reset()
        # After reset, spectral flux should be 0 (no previous frame)
        result = analyzer.analyze(make_sine(440.0))
        assert result.spectral_flux == pytest.approx(0.0, abs=1e-6)


class TestPerformance:
    def test_analysis_speed(self):
        """Analysis of a 1024-sample buffer should take < 2ms."""
        analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        samples = make_sine(440.0)
        # Warm up
        for _ in range(10):
            analyzer.analyze(samples)
        # Time 100 iterations
        start = time.perf_counter()
        iterations = 100
        for _ in range(iterations):
            analyzer.analyze(samples)
        elapsed = time.perf_counter() - start
        avg_ms = (elapsed / iterations) * 1000
        assert avg_ms < 2.0, f"Analysis too slow: {avg_ms:.2f}ms avg (target < 2ms)"


class TestCustomBands:
    def test_custom_band_ranges(self):
        custom_bands = {
            "bass": BandRange(20, 200),
            "treble": BandRange(5000, 20000),
        }
        analyzer = AudioAnalyzer(
            sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE, bands=custom_bands
        )
        result = analyzer.analyze(make_sine(100.0))
        # The result still uses the BandEnergies dataclass with default field names
        # but custom bands are tracked internally
        assert result is not None
