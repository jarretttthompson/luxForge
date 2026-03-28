"""Real-time audio analysis: FFT, band energy, RMS, spectral features."""

import numpy as np
from dataclasses import dataclass

from src.audio.types import AnalysisResult, BandEnergies


@dataclass
class BandRange:
    """Frequency range for a band in Hz."""
    low: float
    high: float


# Default frequency band ranges (Hz)
DEFAULT_BANDS = {
    "sub": BandRange(20, 60),
    "low": BandRange(60, 250),
    "mid": BandRange(250, 2000),
    "hi_mid": BandRange(2000, 6000),
    "high": BandRange(6000, 20000),
}


class AudioAnalyzer:
    """Analyzes audio frames producing frequency and time-domain features.

    All output values are normalized to roughly 0.0-1.0 using running
    min/max tracking with decay, so they adapt to the dynamic range
    of the input signal over time.
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        buffer_size: int = 1024,
        bands: dict[str, BandRange] | None = None,
        normalization_decay: float = 0.999,
    ):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.bands = bands or DEFAULT_BANDS
        self.normalization_decay = normalization_decay

        # Precompute
        self._window = np.hanning(buffer_size).astype(np.float32)
        self._fft_size = buffer_size // 2 + 1
        self._freq_bins = np.fft.rfftfreq(buffer_size, d=1.0 / sample_rate)

        # Precompute band bin indices for fast lookup
        self._band_masks: dict[str, np.ndarray] = {}
        for name, band in self.bands.items():
            self._band_masks[name] = (self._freq_bins >= band.low) & (self._freq_bins < band.high)

        # State for spectral flux (difference between consecutive frames)
        self._prev_magnitudes: np.ndarray | None = None

        # Running normalization state (tracks max values with decay)
        self._band_max: dict[str, float] = {name: 1e-10 for name in self.bands}
        self._rms_max: float = 1e-10
        self._flux_max: float = 1e-10
        self._centroid_max: float = 1e-10

    def analyze(self, samples: np.ndarray) -> AnalysisResult:
        """Analyze a single audio frame.

        Args:
            samples: Mono float32 array of shape (buffer_size,), range [-1.0, 1.0]

        Returns:
            AnalysisResult with all fields populated (beat fields left at defaults).
        """
        # --- Time domain ---
        rms = float(np.sqrt(np.mean(samples ** 2)))
        peak = float(np.max(np.abs(samples)))

        # --- Frequency domain ---
        windowed = samples * self._window
        fft_complex = np.fft.rfft(windowed)
        magnitudes = np.abs(fft_complex).astype(np.float32)

        # --- Band energies ---
        raw_band_energies = {}
        for name, mask in self._band_masks.items():
            band_mags = magnitudes[mask]
            if len(band_mags) > 0:
                raw_band_energies[name] = float(np.mean(band_mags ** 2))
            else:
                raw_band_energies[name] = 0.0

        # --- Spectral centroid ---
        mag_sum = np.sum(magnitudes)
        if mag_sum > 1e-10:
            raw_centroid = float(np.sum(self._freq_bins * magnitudes) / mag_sum)
        else:
            raw_centroid = 0.0

        # --- Spectral flux ---
        if self._prev_magnitudes is not None:
            diff = magnitudes - self._prev_magnitudes
            raw_flux = float(np.sum(np.maximum(diff, 0) ** 2))
        else:
            raw_flux = 0.0
        self._prev_magnitudes = magnitudes.copy()

        # --- Normalize using running max with decay ---
        decay = self.normalization_decay

        # RMS normalization
        self._rms_max = max(rms, self._rms_max * decay)
        norm_rms = rms / self._rms_max if self._rms_max > 1e-10 else 0.0

        # Band energy normalization
        norm_bands = {}
        for name, raw_val in raw_band_energies.items():
            self._band_max[name] = max(raw_val, self._band_max[name] * decay)
            if self._band_max[name] > 1e-10:
                norm_bands[name] = min(raw_val / self._band_max[name], 1.0)
            else:
                norm_bands[name] = 0.0

        # Centroid normalization (normalize to 0-1 based on Nyquist)
        nyquist = self.sample_rate / 2.0
        norm_centroid = min(raw_centroid / nyquist, 1.0) if nyquist > 0 else 0.0

        # Flux normalization
        self._flux_max = max(raw_flux, self._flux_max * decay)
        norm_flux = raw_flux / self._flux_max if self._flux_max > 1e-10 else 0.0

        return AnalysisResult(
            fft_magnitudes=magnitudes,
            band_energies=BandEnergies(
                sub=norm_bands.get("sub", 0.0),
                low=norm_bands.get("low", 0.0),
                mid=norm_bands.get("mid", 0.0),
                hi_mid=norm_bands.get("hi_mid", 0.0),
                high=norm_bands.get("high", 0.0),
            ),
            spectral_centroid=norm_centroid,
            spectral_flux=min(norm_flux, 1.0),
            rms=min(norm_rms, 1.0),
            peak=min(peak, 1.0),
        )

    def reset(self) -> None:
        """Reset internal state (normalization history, previous frame)."""
        self._prev_magnitudes = None
        self._band_max = {name: 1e-10 for name in self.bands}
        self._rms_max = 1e-10
        self._flux_max = 1e-10
        self._centroid_max = 1e-10
