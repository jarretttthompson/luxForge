"""Abstract base class for lighting console interfaces."""

from abc import ABC, abstractmethod

from src.console.types import ConsoleCapability, ConsoleCommand, ParameterDef
from src.protocols.types import ProtocolMessage


class ConsoleInterface(ABC):
    """Abstract interface for a lighting console.

    Translates logical commands (e.g., "set playback 1 fader to 75%")
    into protocol-specific messages (e.g., OSC, MIDI, DMX).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Console name for display and logging."""

    @abstractmethod
    def get_capabilities(self) -> list[ConsoleCapability]:
        """Return the list of capabilities this console supports."""

    @abstractmethod
    def translate(self, command: ConsoleCommand) -> list[ProtocolMessage]:
        """Translate an abstract command into protocol-specific messages.

        Returns a list because one logical command may produce multiple
        protocol messages (e.g., OSC + MIDI simultaneously).
        """

    @abstractmethod
    def get_output_parameters(self) -> dict[str, ParameterDef]:
        """Return all available output parameters for the mapping engine.

        Keys are parameter names like "onyx.playback.1.fader".
        """
