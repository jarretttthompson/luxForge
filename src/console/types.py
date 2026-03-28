"""Console interface types: capabilities, commands, and parameter definitions."""

from dataclasses import dataclass
from enum import Enum


class ConsoleCapability(Enum):
    """What a lighting console can be controlled to do."""
    PLAYBACK_FADER = "playback_fader"
    PLAYBACK_GO = "playback_go"
    PLAYBACK_STOP = "playback_stop"
    DIRECT_DMX = "direct_dmx"
    BUTTON = "button"


@dataclass
class ConsoleCommand:
    """An abstract command to send to a console.

    target: logical name like "playback.1.fader" or "playback.3.go"
    value: 0.0-1.0 for faders, 1.0 for triggers
    command_type: what kind of control this is
    """
    target: str
    value: float
    command_type: ConsoleCapability


@dataclass
class ParameterDef:
    """Definition of an output parameter that the mapping engine can target."""
    name: str                          # e.g. "onyx.playback.1.fader"
    display_name: str                  # e.g. "Playback 1 Fader"
    min_val: float = 0.0
    max_val: float = 1.0
    default_val: float = 0.0
    command_type: ConsoleCapability = ConsoleCapability.PLAYBACK_FADER
