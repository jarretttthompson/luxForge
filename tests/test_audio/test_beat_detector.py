"""Tests for beat detection: onset detection, BPM estimation, beat phase."""

import numpy as np
import pytest

from src.audio.analyzer import AudioAnalyzer
from src.audio.beat_detector import BeatDetector


SAMPLE_RATE = 48000
BUFFER_SIZE = 1024
FRAMES_PER_SECOND = SAMPLE_RATE / BUFFER_SIZE  # ~46.875 fps


def generate_click_track(bpm: float, duration_seconds: float = 8.0) -> list[float]:
    """Generate a synthetic click track as a series of spectral flux values.

    Returns a list of flux values where onsets appear at the correct BPM interval.
    """
    total_frames = int(duration_seconds * FRAMES_PER_SECOND)
    beat_interval_frames = FRAMES_PER_SECOND * 60.0 / bpm
    flux_values = []

    for i in range(total_frames):
        # Generate a spike at each beat position
        beat_pos = i % beat_interval_frames
        if beat_pos < 2:  # Spike lasts ~2 frames
            flux_values.append(0.8 + np.random.uniform(0, 0.1))
        else:
            flux_values.append(np.random.uniform(0, 0.05))  # Background noise

    return flux_values


def generate_flux_from_audio(bpm: float, duration_seconds: float = 8.0) -> list[float]:
    """Generate flux values by running synthetic kick audio through the analyzer."""
    analyzer = AudioAnalyzer(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
    total_frames = int(duration_seconds * FRAMES_PER_SECOND)
    flux_values = []

    beat_period = 60.0 / bpm

    for i in range(total_frames):
        t_start = i * BUFFER_SIZE / SAMPLE_RATE
        t = np.arange(BUFFER_SIZE, dtype=np.float32) / SAMPLE_RATE + t_start

        # Synthesize a kick drum at the given BPM
        beat_pos = (t % beat_period) / beat_period
        kick_env = np.exp(-beat_pos * 30.0)
        kick_freq = 150.0 - 100.0 * beat_pos
        kick_phase = 2.0 * np.pi * np.cumsum(kick_freq / SAMPLE_RATE)
        samples = (np.sin(kick_phase) * kick_env * 0.8).astype(np.float32)

        result = analyzer.analyze(samples)
        flux_values.append(result.spectral_flux)

    return flux_values


class TestOnsetDetection:
    def test_detects_onset_on_spike(self):
        """Should detect onsets when flux spikes above threshold."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        flux_values = generate_click_track(120.0, duration_seconds=4.0)

        onset_count = 0
        for flux in flux_values:
            onset, _, _, _ = detector.process(flux)
            if onset:
                onset_count += 1

        # At 120 BPM for 4 seconds, we expect ~8 beats
        assert onset_count >= 3, f"Too few onsets detected: {onset_count} (expected ~8)"

    def test_no_onsets_on_silence(self):
        """Should not detect onsets in silence/low noise."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        onset_count = 0
        for _ in range(200):
            onset, _, _, _ = detector.process(0.01)
            if onset:
                onset_count += 1
        assert onset_count == 0, f"False onsets in silence: {onset_count}"

    def test_no_onsets_on_constant_signal(self):
        """Should not detect onsets on a constant flux value."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        onset_count = 0
        for _ in range(200):
            onset, _, _, _ = detector.process(0.5)
            if onset:
                onset_count += 1
        # After the initial transient, should settle
        assert onset_count < 5, f"Too many onsets on constant signal: {onset_count}"


class TestBPMEstimation:
    def test_estimates_120_bpm(self):
        """Should estimate ~120 BPM from a 120 BPM click track."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        flux_values = generate_click_track(120.0, duration_seconds=10.0)

        for flux in flux_values:
            detector.process(flux)

        estimated = detector.bpm
        # Allow ±15 BPM tolerance (autocorrelation has limited resolution)
        assert 100 < estimated < 140, f"BPM estimate {estimated:.1f} too far from 120"

    def test_estimates_90_bpm(self):
        """Should estimate ~90 BPM from a 90 BPM click track."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        flux_values = generate_click_track(90.0, duration_seconds=12.0)

        for flux in flux_values:
            detector.process(flux)

        estimated = detector.bpm
        assert 70 < estimated < 110, f"BPM estimate {estimated:.1f} too far from 90"

    def test_bpm_zero_initially(self):
        """BPM should be 0 before enough data is collected."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        assert detector.bpm == 0.0

    def test_bpm_stays_in_range(self):
        """BPM estimate should always be within configured range."""
        detector = BeatDetector(
            sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE,
            min_bpm=60.0, max_bpm=200.0,
        )
        flux_values = generate_click_track(120.0, duration_seconds=10.0)
        for flux in flux_values:
            detector.process(flux)

        if detector.bpm > 0:
            assert 60.0 <= detector.bpm <= 200.0


class TestBeatPhase:
    def test_beat_phase_in_range(self):
        """Beat phase should always be in [0.0, 1.0)."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        flux_values = generate_click_track(120.0, duration_seconds=6.0)

        for flux in flux_values:
            _, _, _, phase = detector.process(flux)
            assert 0.0 <= phase <= 1.0, f"Phase out of range: {phase}"

    def test_beat_detected_events_occur(self):
        """Should produce beat_detected events once BPM is locked."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        flux_values = generate_click_track(120.0, duration_seconds=10.0)

        beat_count = 0
        for flux in flux_values:
            _, beat, _, _ = detector.process(flux)
            if beat:
                beat_count += 1

        # At 120 BPM for 10 seconds, expect ~20 beats, but detection starts late
        assert beat_count >= 5, f"Too few beats detected: {beat_count}"


class TestReset:
    def test_reset_clears_all_state(self):
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        # Build up state
        flux_values = generate_click_track(120.0, duration_seconds=6.0)
        for flux in flux_values:
            detector.process(flux)

        detector.reset()
        assert detector.bpm == 0.0
        assert detector.confidence == 0.0


class TestWithRealAnalyzer:
    def test_full_pipeline_kick_pattern(self):
        """End-to-end test: synthetic kicks → analyzer → beat detector."""
        detector = BeatDetector(sample_rate=SAMPLE_RATE, buffer_size=BUFFER_SIZE)
        flux_values = generate_flux_from_audio(120.0, duration_seconds=10.0)

        onset_count = 0
        for flux in flux_values:
            onset, _, _, _ = detector.process(flux)
            if onset:
                onset_count += 1

        # Should detect some onsets from the kick pattern
        assert onset_count >= 3, f"Too few onsets from kick audio: {onset_count}"
