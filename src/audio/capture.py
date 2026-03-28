"""Audio capture from hardware devices via sounddevice."""

import threading
import time
import numpy as np
import structlog
import sounddevice as sd

from src.audio.types import AudioFrame

logger = structlog.get_logger()


class RingBuffer:
    """Lock-free single-producer single-consumer ring buffer for audio frames."""

    def __init__(self, capacity: int, frame_size: int):
        self._buffer = np.zeros((capacity, frame_size), dtype=np.float32)
        self._capacity = capacity
        self._write_idx = 0
        self._read_idx = 0
        self._count = 0
        self._lock = threading.Lock()

    def write(self, frame: np.ndarray) -> None:
        """Write a frame to the buffer (called from audio thread)."""
        with self._lock:
            self._buffer[self._write_idx % self._capacity] = frame
            self._write_idx += 1
            self._count = min(self._count + 1, self._capacity)

    def read(self) -> np.ndarray | None:
        """Read the latest frame from the buffer. Returns None if empty."""
        with self._lock:
            if self._count == 0:
                return None
            idx = (self._write_idx - 1) % self._capacity
            frame = self._buffer[idx].copy()
            self._count = 0  # Mark as consumed
            self._read_idx = self._write_idx
            return frame

    @property
    def has_data(self) -> bool:
        with self._lock:
            return self._count > 0


class AudioCapture:
    """Captures audio from a hardware device using sounddevice."""

    def __init__(
        self,
        device_index: int | None = None,
        sample_rate: int = 48000,
        buffer_size: int = 1024,
        ring_buffer_capacity: int = 16,
    ):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.ring_buffer = RingBuffer(ring_buffer_capacity, buffer_size)

        self._stream: sd.InputStream | None = None
        self._start_time: float = 0.0
        self._running = False

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status) -> None:
        """Called by sounddevice from the audio thread."""
        if status:
            logger.warning("audio_callback_status", status=str(status))
        # Mix to mono if stereo, convert to float32
        if indata.ndim > 1:
            mono = indata.mean(axis=1).astype(np.float32)
        else:
            mono = indata[:, 0].astype(np.float32) if indata.ndim == 1 else indata.astype(np.float32)

        # Ensure correct size
        if len(mono) == self.buffer_size:
            self.ring_buffer.write(mono)

    def start(self) -> None:
        """Start capturing audio from the configured device."""
        if self._running:
            return

        logger.info(
            "audio_capture_start",
            device=self.device_index,
            sample_rate=self.sample_rate,
            buffer_size=self.buffer_size,
        )

        self._start_time = time.monotonic()
        self._stream = sd.InputStream(
            device=self.device_index,
            samplerate=self.sample_rate,
            blocksize=self.buffer_size,
            channels=1,
            dtype="float32",
            callback=self._audio_callback,
        )
        self._stream.start()
        self._running = True

    def stop(self) -> None:
        """Stop capturing audio."""
        if not self._running:
            return
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._running = False
        logger.info("audio_capture_stopped")

    def read_frame(self) -> AudioFrame | None:
        """Read the latest audio frame. Returns None if no new data."""
        samples = self.ring_buffer.read()
        if samples is None:
            return None
        return AudioFrame(
            samples=samples,
            sample_rate=self.sample_rate,
            timestamp=time.monotonic() - self._start_time,
        )

    @property
    def is_running(self) -> bool:
        return self._running

    @staticmethod
    def list_devices() -> list[dict]:
        """List all available audio input devices."""
        devices = sd.query_devices()
        inputs = []
        for i, dev in enumerate(devices):
            if dev["max_input_channels"] > 0:
                inputs.append({
                    "index": i,
                    "name": dev["name"],
                    "channels": dev["max_input_channels"],
                    "sample_rate": dev["default_samplerate"],
                })
        return inputs
