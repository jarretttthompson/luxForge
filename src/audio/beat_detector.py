"""Beat detection: onset detection, BPM estimation, and beat phase tracking."""

import numpy as np
import structlog

logger = structlog.get_logger()


class BeatDetector:
    """Detects beats from spectral flux data.

    Algorithm:
    1. Onset detection: spectral flux exceeding adaptive threshold
       (median + multiplier * median absolute deviation of recent flux values)
    2. BPM estimation: autocorrelation of the onset function over a sliding window
    3. Beat phase: tracks expected beat positions, reports phase 0.0-1.0
    """

    def __init__(
        self,
        sample_rate: int = 48000,
        buffer_size: int = 1024,
        history_seconds: float = 8.0,
        onset_threshold_multiplier: float = 1.5,
        min_bpm: float = 60.0,
        max_bpm: float = 200.0,
    ):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.onset_threshold_multiplier = onset_threshold_multiplier
        self.min_bpm = min_bpm
        self.max_bpm = max_bpm

        # How many analysis frames fit in the history window
        self._frames_per_second = sample_rate / buffer_size
        self._history_length = int(history_seconds * self._frames_per_second)

        # Onset detection state
        self._flux_history: list[float] = []
        self._onset_history: list[float] = []  # 1.0 for onset, 0.0 for no onset

        # BPM estimation state
        self._current_bpm: float = 0.0
        self._bpm_confidence: float = 0.0

        # Beat phase tracking state
        self._phase_accumulator: float = 0.0
        self._last_beat_frame: int = 0
        self._frame_counter: int = 0

        # Cooldown to prevent double-triggering (minimum frames between onsets)
        self._min_onset_interval = int(self._frames_per_second * 60.0 / max_bpm * 0.5)
        self._frames_since_last_onset: int = self._min_onset_interval

    def process(self, spectral_flux: float) -> tuple[bool, bool, float, float]:
        """Process one frame of spectral flux data.

        Args:
            spectral_flux: Spectral flux value from the analyzer (0.0-1.0 normalized)

        Returns:
            Tuple of (onset_detected, beat_detected, bpm, beat_phase)
        """
        self._frame_counter += 1
        self._frames_since_last_onset += 1

        # --- Onset Detection ---
        self._flux_history.append(spectral_flux)
        if len(self._flux_history) > self._history_length:
            self._flux_history = self._flux_history[-self._history_length:]

        onset_detected = self._detect_onset(spectral_flux)
        self._onset_history.append(1.0 if onset_detected else 0.0)
        if len(self._onset_history) > self._history_length:
            self._onset_history = self._onset_history[-self._history_length:]

        # --- BPM Estimation ---
        if len(self._onset_history) >= int(self._frames_per_second * 2):
            self._estimate_bpm()

        # --- Beat Phase Tracking ---
        beat_detected = False
        beat_phase = 0.0

        if self._current_bpm > 0:
            beat_period_frames = self._frames_per_second * 60.0 / self._current_bpm
            if beat_period_frames > 0:
                self._phase_accumulator += 1.0 / beat_period_frames
                beat_phase = self._phase_accumulator % 1.0

                # Beat occurs when phase wraps around
                if self._phase_accumulator >= 1.0:
                    beat_detected = True
                    self._phase_accumulator %= 1.0

                # Resync phase on strong onsets
                if onset_detected and self._bpm_confidence > 0.3:
                    self._phase_accumulator = 0.0
                    beat_phase = 0.0
                    beat_detected = True

        return onset_detected, beat_detected, self._current_bpm, beat_phase

    def _detect_onset(self, flux: float) -> bool:
        """Detect onset using adaptive threshold on spectral flux."""
        if len(self._flux_history) < 10:
            return False

        if self._frames_since_last_onset < self._min_onset_interval:
            return False

        recent = np.array(self._flux_history[-50:] if len(self._flux_history) >= 50
                          else self._flux_history)
        median = float(np.median(recent))
        mad = float(np.median(np.abs(recent - median)))

        threshold = median + self.onset_threshold_multiplier * max(mad, 0.01)

        if flux > threshold and flux > 0.05:
            self._frames_since_last_onset = 0
            return True
        return False

    def _estimate_bpm(self) -> None:
        """Estimate BPM using autocorrelation of the onset function."""
        onset_arr = np.array(self._onset_history, dtype=np.float32)

        # Autocorrelation
        n = len(onset_arr)
        if n < 20:
            return

        # Lag range corresponding to min/max BPM
        min_lag = max(1, int(self._frames_per_second * 60.0 / self.max_bpm))
        max_lag = min(n // 2, int(self._frames_per_second * 60.0 / self.min_bpm))

        if min_lag >= max_lag:
            return

        # Compute autocorrelation for the lag range
        mean = np.mean(onset_arr)
        centered = onset_arr - mean
        norm = np.sum(centered ** 2)
        if norm < 1e-10:
            return

        correlations = np.zeros(max_lag - min_lag)
        for i, lag in enumerate(range(min_lag, max_lag)):
            correlations[i] = np.sum(centered[:n - lag] * centered[lag:]) / norm

        if len(correlations) == 0:
            return

        # Find the peak
        peak_idx = np.argmax(correlations)
        peak_value = correlations[peak_idx]
        best_lag = peak_idx + min_lag

        if best_lag > 0 and peak_value > 0.1:
            estimated_bpm = (self._frames_per_second * 60.0) / best_lag
            # Clamp to valid range
            estimated_bpm = max(self.min_bpm, min(self.max_bpm, estimated_bpm))

            # Smooth the BPM estimate
            if self._current_bpm > 0:
                # Weighted average favoring the new estimate when confidence is high
                weight = min(peak_value, 0.3)
                self._current_bpm = self._current_bpm * (1 - weight) + estimated_bpm * weight
            else:
                self._current_bpm = estimated_bpm

            self._bpm_confidence = float(peak_value)

    def reset(self) -> None:
        """Reset all internal state."""
        self._flux_history.clear()
        self._onset_history.clear()
        self._current_bpm = 0.0
        self._bpm_confidence = 0.0
        self._phase_accumulator = 0.0
        self._frame_counter = 0
        self._frames_since_last_onset = self._min_onset_interval

    @property
    def bpm(self) -> float:
        return self._current_bpm

    @property
    def confidence(self) -> float:
        return self._bpm_confidence
