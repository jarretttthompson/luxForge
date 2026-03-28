"""Shared test fixtures."""

import numpy as np
import pytest


@pytest.fixture
def sample_rate() -> int:
    return 48000


@pytest.fixture
def buffer_size() -> int:
    return 1024


@pytest.fixture
def silence(buffer_size: int) -> np.ndarray:
    """A buffer of silence."""
    return np.zeros(buffer_size, dtype=np.float32)


@pytest.fixture
def sine_wave(sample_rate: int, buffer_size: int) -> callable:
    """Factory fixture to generate a sine wave at a given frequency."""
    def _make(frequency: float = 440.0, amplitude: float = 1.0) -> np.ndarray:
        t = np.arange(buffer_size, dtype=np.float32) / sample_rate
        return (np.sin(2 * np.pi * frequency * t) * amplitude).astype(np.float32)
    return _make
