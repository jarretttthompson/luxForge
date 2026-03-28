"""Audio simulator for hardware-free development and testing.

Generates synthetic audio signals that feed into the same pipeline
as real hardware audio. Implements the same interface as AudioCapture.
"""

import threading
import time
import numpy as np
import structlog

from src.audio.types import AudioFrame
from src.audio.capture import RingBuffer

logger = structlog.get_logger()


class AudioSimulator:
    """Generates synthetic audio signals. Drop-in replacement for AudioCapture."""

    MODES = ("kick_pattern", "sine", "noise", "sweep", "silent")

    def __init__(
        self,
        mode: str = "kick_pattern",
        sample_rate: int = 48000,
        buffer_size: int = 1024,
        bpm: int = 120,
        frequency: float = 440.0,
        ring_buffer_capacity: int = 16,
    ):
        if mode not in self.MODES:
            raise ValueError(f"Unknown mode '{mode}'. Choose from: {self.MODES}")

        self.mode = mode
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.bpm = bpm
        self.frequency = frequency
        self.ring_buffer = RingBuffer(ring_buffer_capacity, buffer_size)

        self._thread: threading.Thread | None = None
        self._running = False
        self._start_time: float = 0.0
        self._phase: float = 0.0  # For continuous waveform generation
        self._sample_counter: int = 0

    def _generate_kick(self, t_start: float, num_samples: int) -> np.ndarray:
        """Generate a synthetic kick drum pattern at the configured BPM."""
        t = np.arange(num_samples, dtype=np.float32) / self.sample_rate + t_start
        beat_period = 60.0 / self.bpm
        # Position within current beat (0.0 to 1.0)
        beat_pos = (t % beat_period) / beat_period
        # Kick: fast frequency sweep from 150Hz down to 50Hz, with exponential decay
        kick_env = np.exp(-beat_pos * 30.0)  # Sharp decay
        kick_freq = 150.0 - 100.0 * beat_pos  # Frequency sweep
        kick_phase = 2.0 * np.pi * np.cumsum(kick_freq / self.sample_rate)
        signal = (np.sin(kick_phase) * kick_env * 0.8).astype(np.float32)
        return signal

    def _generate_sine(self, num_samples: int) -> np.ndarray:
        """Generate a pure sine wave at the configured frequency."""
        t = np.arange(num_samples, dtype=np.float32) / self.sample_rate
        phase_increment = 2.0 * np.pi * self.frequency / self.sample_rate
        phases = self._phase + np.arange(num_samples) * phase_increment
        self._phase = phases[-1] + phase_increment
        signal = (np.sin(phases) * 0.7).astype(np.float32)
        return signal

    def _generate_noise(self, num_samples: int) -> np.ndarray:
        """Generate white noise."""
        return (np.random.randn(num_samples).astype(np.float32) * 0.3)

    def _generate_sweep(self, t_start: float, num_samples: int) -> np.ndarray:
        """Generate a frequency sweep from 20Hz to 20kHz over 5 seconds, repeating."""
        t = np.arange(num_samples, dtype=np.float32) / self.sample_rate + t_start
        sweep_period = 5.0
        sweep_pos = (t % sweep_period) / sweep_period
        freq = 20.0 * (1000.0 ** sweep_pos)  # Logarithmic sweep
        phase = 2.0 * np.pi * np.cumsum(freq / self.sample_rate)
        signal = (np.sin(phase) * 0.5).astype(np.float32)
        return signal

    def _generate_frame(self) -> np.ndarray:
        """Generate one buffer's worth of audio samples."""
        t_start = self._sample_counter / self.sample_rate
        n = self.buffer_size

        if self.mode == "kick_pattern":
            frame = self._generate_kick(t_start, n)
        elif self.mode == "sine":
            frame = self._generate_sine(n)
        elif self.mode == "noise":
            frame = self._generate_noise(n)
        elif self.mode == "sweep":
            frame = self._generate_sweep(t_start, n)
        elif self.mode == "silent":
            frame = np.zeros(n, dtype=np.float32)
        else:
            frame = np.zeros(n, dtype=np.float32)

        self._sample_counter += n
        return frame

    def _run(self) -> None:
        """Main loop that generates audio at the correct sample rate."""
        interval = self.buffer_size / self.sample_rate  # Time per buffer
        next_time = time.monotonic()

        while self._running:
            frame = self._generate_frame()
            self.ring_buffer.write(frame)

            next_time += interval
            sleep_time = next_time - time.monotonic()
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self) -> None:
        """Start generating audio."""
        if self._running:
            return

        logger.info(
            "audio_simulator_start",
            mode=self.mode,
            bpm=self.bpm,
            sample_rate=self.sample_rate,
            buffer_size=self.buffer_size,
        )

        self._start_time = time.monotonic()
        self._sample_counter = 0
        self._phase = 0.0
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="audio-simulator")
        self._thread.start()

    def stop(self) -> None:
        """Stop generating audio."""
        if not self._running:
            return
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("audio_simulator_stopped")

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
        """Returns simulator as the only available device."""
        return [{
            "index": -1,
            "name": "Audio Simulator",
            "channels": 1,
            "sample_rate": 48000.0,
        }]
