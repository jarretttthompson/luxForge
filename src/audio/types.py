"""Audio data types used throughout the audio pipeline."""

from dataclasses import dataclass, field
import numpy as np


@dataclass
class AudioFrame:
    """A raw audio frame from capture or simulator."""

    samples: np.ndarray  # Shape: (buffer_size,) mono float32, range [-1.0, 1.0]
    sample_rate: int
    timestamp: float  # Time in seconds since capture started


@dataclass
class BandEnergies:
    """Energy levels per frequency band, normalized to 0.0-1.0."""

    sub: float = 0.0       # 20-60 Hz
    low: float = 0.0       # 60-250 Hz
    mid: float = 0.0       # 250-2000 Hz
    hi_mid: float = 0.0    # 2000-6000 Hz
    high: float = 0.0      # 6000-20000 Hz


@dataclass
class AnalysisResult:
    """Complete audio analysis output for a single frame."""

    # Frequency domain
    fft_magnitudes: np.ndarray = field(default_factory=lambda: np.zeros(512))
    band_energies: BandEnergies = field(default_factory=BandEnergies)
    spectral_centroid: float = 0.0
    spectral_flux: float = 0.0

    # Time domain
    rms: float = 0.0
    peak: float = 0.0

    # Beat detection
    beat_detected: bool = False
    bpm: float = 0.0
    beat_phase: float = 0.0  # 0.0-1.0 within current beat period
    onset_detected: bool = False

    # Metadata
    timestamp: float = 0.0
