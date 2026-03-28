"""Parameter registry: tracks all available input and output parameters."""

from dataclasses import dataclass

from src.audio.types import AnalysisResult, BandEnergies
from src.console.base import ConsoleInterface
from src.console.types import ParameterDef


@dataclass
class InputParamDef:
    """Definition of an input parameter from audio analysis."""
    name: str
    display_name: str


# All audio input parameters that the mapping engine can read
AUDIO_INPUT_PARAMS: list[InputParamDef] = [
    InputParamDef("audio.rms", "RMS Level"),
    InputParamDef("audio.peak", "Peak Level"),
    InputParamDef("audio.band.sub", "Sub Band (20-60Hz)"),
    InputParamDef("audio.band.low", "Low Band (60-250Hz)"),
    InputParamDef("audio.band.mid", "Mid Band (250-2kHz)"),
    InputParamDef("audio.band.hi_mid", "Hi-Mid Band (2k-6kHz)"),
    InputParamDef("audio.band.high", "High Band (6k-20kHz)"),
    InputParamDef("audio.bpm", "BPM"),
    InputParamDef("audio.beat", "Beat Detected"),
    InputParamDef("audio.onset", "Onset Detected"),
    InputParamDef("audio.beat_phase", "Beat Phase"),
    InputParamDef("audio.spectral_centroid", "Spectral Centroid"),
    InputParamDef("audio.spectral_flux", "Spectral Flux"),
]


class ParameterRegistry:
    """Registry of all available input and output parameters.

    Input parameters come from audio analysis (fixed set).
    Output parameters come from the active console interface (dynamic).
    """

    def __init__(self):
        self._inputs: dict[str, InputParamDef] = {}
        self._outputs: dict[str, ParameterDef] = {}

        # Register default audio inputs
        for param in AUDIO_INPUT_PARAMS:
            self._inputs[param.name] = param

    def register_console(self, console: ConsoleInterface) -> None:
        """Populate output parameters from a console interface."""
        self._outputs.update(console.get_output_parameters())

    def register_output(self, name: str, param_def: ParameterDef) -> None:
        """Manually register an output parameter."""
        self._outputs[name] = param_def

    @property
    def inputs(self) -> dict[str, InputParamDef]:
        return dict(self._inputs)

    @property
    def outputs(self) -> dict[str, ParameterDef]:
        return dict(self._outputs)

    def has_input(self, name: str) -> bool:
        return name in self._inputs

    def has_output(self, name: str) -> bool:
        return name in self._outputs

    @staticmethod
    def resolve_input(name: str, analysis: AnalysisResult) -> float:
        """Read an input parameter value from an AnalysisResult.

        Supports dotted paths like "audio.band.sub", "audio.rms", etc.
        """
        parts = name.split(".")
        if len(parts) < 2 or parts[0] != "audio":
            return 0.0

        field = parts[1]

        if field == "rms":
            return analysis.rms
        elif field == "peak":
            return analysis.peak
        elif field == "bpm":
            # Normalize BPM to 0-1 range (0-200 BPM -> 0-1)
            return min(analysis.bpm / 200.0, 1.0)
        elif field == "beat":
            return 1.0 if analysis.beat_detected else 0.0
        elif field == "onset":
            return 1.0 if analysis.onset_detected else 0.0
        elif field == "beat_phase":
            return analysis.beat_phase
        elif field == "spectral_centroid":
            return analysis.spectral_centroid
        elif field == "spectral_flux":
            return analysis.spectral_flux
        elif field == "band" and len(parts) == 3:
            band_name = parts[2]
            return getattr(analysis.band_energies, band_name, 0.0)

        return 0.0
