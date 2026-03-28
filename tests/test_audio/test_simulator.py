"""Tests for the audio simulator."""

import time
import numpy as np
import pytest

from src.audio.simulator import AudioSimulator


class TestAudioSimulator:
    def test_invalid_mode_raises(self):
        with pytest.raises(ValueError, match="Unknown mode"):
            AudioSimulator(mode="invalid")

    def test_valid_modes(self):
        for mode in AudioSimulator.MODES:
            sim = AudioSimulator(mode=mode)
            assert sim.mode == mode

    def test_generate_kick_not_silent(self):
        sim = AudioSimulator(mode="kick_pattern", bpm=120, sample_rate=48000, buffer_size=1024)
        frame = sim._generate_frame()
        assert frame.dtype == np.float32
        assert len(frame) == 1024
        assert np.max(np.abs(frame)) > 0.01  # Not silence

    def test_generate_sine_correct_shape(self):
        sim = AudioSimulator(mode="sine", frequency=440.0, sample_rate=48000, buffer_size=1024)
        frame = sim._generate_frame()
        assert frame.dtype == np.float32
        assert len(frame) == 1024
        assert np.max(np.abs(frame)) > 0.5

    def test_generate_noise_not_silent(self):
        sim = AudioSimulator(mode="noise", sample_rate=48000, buffer_size=1024)
        frame = sim._generate_frame()
        assert len(frame) == 1024
        assert np.std(frame) > 0.1

    def test_generate_sweep_not_silent(self):
        sim = AudioSimulator(mode="sweep", sample_rate=48000, buffer_size=1024)
        frame = sim._generate_frame()
        assert len(frame) == 1024
        assert np.max(np.abs(frame)) > 0.1

    def test_generate_silent_is_silent(self):
        sim = AudioSimulator(mode="silent", sample_rate=48000, buffer_size=1024)
        frame = sim._generate_frame()
        assert len(frame) == 1024
        np.testing.assert_array_equal(frame, np.zeros(1024, dtype=np.float32))

    def test_start_stop_lifecycle(self):
        sim = AudioSimulator(mode="sine", sample_rate=48000, buffer_size=1024)
        assert sim.is_running is False
        sim.start()
        assert sim.is_running is True
        time.sleep(0.1)  # Let it generate a few frames
        sim.stop()
        assert sim.is_running is False

    def test_read_frame_after_generation(self):
        sim = AudioSimulator(mode="sine", sample_rate=48000, buffer_size=1024)
        sim.start()
        time.sleep(0.1)  # Let it generate frames
        frame = sim.read_frame()
        sim.stop()
        assert frame is not None
        assert frame.sample_rate == 48000
        assert len(frame.samples) == 1024

    def test_list_devices_returns_simulator(self):
        devices = AudioSimulator.list_devices()
        assert len(devices) == 1
        assert devices[0]["name"] == "Audio Simulator"

    def test_kick_amplitude_in_range(self):
        sim = AudioSimulator(mode="kick_pattern", bpm=120, sample_rate=48000, buffer_size=1024)
        # Generate several frames
        for _ in range(10):
            frame = sim._generate_frame()
            assert np.all(np.abs(frame) <= 1.0), "Signal exceeds [-1, 1] range"
