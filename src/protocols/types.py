"""Protocol message types for outbound lighting control adapters."""

from dataclasses import dataclass, field
from typing import Literal
import time


ProtocolArg = float | int | str
MIDIMessageType = Literal["note_on", "note_off", "cc"]


@dataclass
class ProtocolMessage:
    """Base protocol message with creation timestamp."""

    timestamp: float = field(default_factory=time.time)


@dataclass
class OSCMessage(ProtocolMessage):
    """OSC address with positional arguments."""

    address: str = ""
    args: list[ProtocolArg] = field(default_factory=list)


@dataclass
class DMXFrame(ProtocolMessage):
    """DMX channel values for a single universe."""

    universe: int = 0
    channels: dict[int, int] = field(default_factory=dict)


@dataclass
class MIDIMessage(ProtocolMessage):
    """MIDI note or control change message."""

    type: MIDIMessageType = "cc"
    channel: int = 0
    note_or_cc: int = 0
    value: int = 0
