"""Tests for audio capture and ring buffer."""

import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from src.audio.capture import RingBuffer, AudioCapture


class TestRingBuffer:
    def test_empty_read_returns_none(self):
        rb = RingBuffer(capacity=4, frame_size=1024)
        assert rb.read() is None

    def test_has_data_initially_false(self):
        rb = RingBuffer(capacity=4, frame_size=1024)
        assert rb.has_data is False

    def test_write_then_read(self):
        rb = RingBuffer(capacity=4, frame_size=8)
        frame = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], dtype=np.float32)
        rb.write(frame)
        assert rb.has_data is True
        result = rb.read()
        assert result is not None
        np.testing.assert_array_equal(result, frame)

    def test_read_consumes_data(self):
        rb = RingBuffer(capacity=4, frame_size=8)
        frame = np.ones(8, dtype=np.float32)
        rb.write(frame)
        rb.read()
        assert rb.has_data is False
        assert rb.read() is None

    def test_read_returns_latest_frame(self):
        rb = RingBuffer(capacity=4, frame_size=4)
        rb.write(np.array([1, 1, 1, 1], dtype=np.float32))
        rb.write(np.array([2, 2, 2, 2], dtype=np.float32))
        rb.write(np.array([3, 3, 3, 3], dtype=np.float32))
        result = rb.read()
        np.testing.assert_array_equal(result, [3, 3, 3, 3])

    def test_wraps_around_capacity(self):
        rb = RingBuffer(capacity=2, frame_size=4)
        for i in range(5):
            rb.write(np.full(4, float(i), dtype=np.float32))
        result = rb.read()
        np.testing.assert_array_equal(result, [4.0, 4.0, 4.0, 4.0])

    def test_read_returns_copy(self):
        rb = RingBuffer(capacity=4, frame_size=4)
        rb.write(np.array([1, 2, 3, 4], dtype=np.float32))
        a = rb.read()
        rb.write(np.array([5, 6, 7, 8], dtype=np.float32))
        # Original read should not be affected
        np.testing.assert_array_equal(a, [1, 2, 3, 4])


class TestAudioCapture:
    def test_list_devices_returns_list(self):
        with patch("src.audio.capture.sd.query_devices") as mock_query:
            mock_query.return_value = [
                {"name": "Test Mic", "max_input_channels": 2, "default_samplerate": 48000.0, "max_output_channels": 0},
                {"name": "Speakers", "max_input_channels": 0, "default_samplerate": 48000.0, "max_output_channels": 2},
            ]
            devices = AudioCapture.list_devices()
            assert len(devices) == 1
            assert devices[0]["name"] == "Test Mic"
            assert devices[0]["index"] == 0
            assert devices[0]["channels"] == 2

    def test_list_devices_empty(self):
        with patch("src.audio.capture.sd.query_devices") as mock_query:
            mock_query.return_value = []
            devices = AudioCapture.list_devices()
            assert devices == []

    def test_initial_state(self):
        cap = AudioCapture.__new__(AudioCapture)
        cap.device_index = None
        cap.sample_rate = 48000
        cap.buffer_size = 1024
        cap.ring_buffer = RingBuffer(16, 1024)
        cap._stream = None
        cap._start_time = 0.0
        cap._running = False
        assert cap.is_running is False
        assert cap.read_frame() is None

    def test_audio_callback_mono(self):
        cap = AudioCapture(sample_rate=48000, buffer_size=4)
        # Simulate mono input
        indata = np.array([[0.1], [0.2], [0.3], [0.4]], dtype=np.float32)
        cap._audio_callback(indata, 4, None, None)
        frame = cap.ring_buffer.read()
        assert frame is not None
        assert len(frame) == 4

    def test_audio_callback_stereo_mixes_to_mono(self):
        cap = AudioCapture(sample_rate=48000, buffer_size=4)
        # Simulate stereo: left=1.0, right=0.0 -> mono=0.5
        indata = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [1.0, 0.0]], dtype=np.float32)
        cap._audio_callback(indata, 4, None, None)
        frame = cap.ring_buffer.read()
        assert frame is not None
        np.testing.assert_allclose(frame, [0.5, 0.5, 0.5, 0.5], atol=1e-6)

    def test_read_frame_returns_audio_frame(self):
        cap = AudioCapture(sample_rate=48000, buffer_size=4)
        cap._start_time = 0.0
        cap.ring_buffer.write(np.array([0.1, 0.2, 0.3, 0.4], dtype=np.float32))
        frame = cap.read_frame()
        assert frame is not None
        assert frame.sample_rate == 48000
        assert len(frame.samples) == 4
