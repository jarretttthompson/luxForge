"""Global application state with thread-safe access."""

import asyncio
from dataclasses import dataclass, field

from src.audio.types import AnalysisResult
from src.mapping.types import MappingRule, OutputValue


@dataclass
class ProtocolStatus:
    """Connection status for a protocol adapter."""
    name: str
    connected: bool = False
    dry_run: bool = False
    messages_sent: int = 0


@dataclass
class AppState:
    """Centralized application state, updated by the engine loop.

    Read by the WebSocket broadcaster and API routes.
    Written by the engine loop (single writer, multiple readers).
    """

    # Audio analysis
    analysis: AnalysisResult = field(default_factory=AnalysisResult)

    # Mapping
    active_rules: list[MappingRule] = field(default_factory=list)
    latest_outputs: list[OutputValue] = field(default_factory=list)

    # Console
    active_console: str = "none"
    active_scene: str | None = None

    # Protocols
    protocol_statuses: dict[str, ProtocolStatus] = field(default_factory=dict)

    # Engine
    engine_running: bool = False
    tick_count: int = 0
    fps: float = 0.0

    # Lock for thread safety when audio thread writes analysis
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    async def update_analysis(self, analysis: AnalysisResult) -> None:
        """Update the current analysis result (called from engine loop)."""
        async with self._lock:
            self.analysis = analysis

    async def update_outputs(self, outputs: list[OutputValue]) -> None:
        """Update the latest mapping outputs."""
        async with self._lock:
            self.latest_outputs = outputs

    def to_snapshot(self) -> dict:
        """Create a JSON-serializable snapshot for WebSocket broadcast.

        Downsamples FFT to 64 bins for efficient transmission.
        """
        analysis = self.analysis
        fft = analysis.fft_magnitudes
        # Downsample FFT to 64 bins by averaging
        if len(fft) > 64:
            chunk_size = len(fft) // 64
            fft_downsampled = [
                float(fft[i * chunk_size:(i + 1) * chunk_size].mean())
                for i in range(64)
            ]
        else:
            fft_downsampled = [float(v) for v in fft]

        return {
            "audio": {
                "fft": fft_downsampled,
                "bands": {
                    "sub": analysis.band_energies.sub,
                    "low": analysis.band_energies.low,
                    "mid": analysis.band_energies.mid,
                    "hi_mid": analysis.band_energies.hi_mid,
                    "high": analysis.band_energies.high,
                },
                "rms": analysis.rms,
                "peak": analysis.peak,
                "bpm": analysis.bpm,
                "beat": analysis.beat_detected,
                "beat_phase": analysis.beat_phase,
                "onset": analysis.onset_detected,
                "spectral_centroid": analysis.spectral_centroid,
            },
            "outputs": [
                {"target": o.target, "value": o.value}
                for o in self.latest_outputs
            ],
            "engine": {
                "running": self.engine_running,
                "fps": round(self.fps, 1),
                "tick_count": self.tick_count,
            },
            "console": self.active_console,
            "scene": self.active_scene,
            "protocols": {
                name: {
                    "connected": s.connected,
                    "dry_run": s.dry_run,
                    "messages_sent": s.messages_sent,
                }
                for name, s in self.protocol_statuses.items()
            },
        }
