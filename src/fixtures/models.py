from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChannelType(str, Enum):
    DIMMER = "DIMMER"
    RED = "RED"
    GREEN = "GREEN"
    BLUE = "BLUE"
    WHITE = "WHITE"
    AMBER = "AMBER"
    UV = "UV"
    PAN = "PAN"
    TILT = "TILT"
    PAN_FINE = "PAN_FINE"
    TILT_FINE = "TILT_FINE"
    GOBO = "GOBO"
    STROBE = "STROBE"
    COLOR_WHEEL = "COLOR_WHEEL"
    ZOOM = "ZOOM"
    FOCUS = "FOCUS"
    PRISM = "PRISM"
    FROST = "FROST"
    SHUTTER = "SHUTTER"
    SPEED = "SPEED"
    COLOR_MACRO = "COLOR_MACRO"
    MODE = "MODE"


@dataclass
class ChannelDef:
    offset: int
    name: str
    channel_type: ChannelType
    min_val: int = 0
    max_val: int = 255
    default_val: int = 0

    def to_dict(self) -> dict:
        return {
            "offset": self.offset,
            "name": self.name,
            "channel_type": self.channel_type.value,
            "min_val": self.min_val,
            "max_val": self.max_val,
            "default_val": self.default_val,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ChannelDef":
        return cls(
            offset=int(data["offset"]),
            name=str(data["name"]),
            channel_type=ChannelType(data["channel_type"]),
            min_val=int(data.get("min_val", 0)),
            max_val=int(data.get("max_val", 255)),
            default_val=int(data.get("default_val", 0)),
        )


@dataclass
class FixtureMode:
    name: str
    channels: list[ChannelDef]

    @property
    def channel_count(self) -> int:
        if not self.channels:
            return 0
        return max(ch.offset for ch in self.channels) + 1

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "channels": [channel.to_dict() for channel in self.channels],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FixtureMode":
        return cls(
            name=str(data["name"]),
            channels=[ChannelDef.from_dict(channel) for channel in data.get("channels", [])],
        )


@dataclass
class FixtureProfile:
    id: str
    manufacturer: str
    name: str
    modes: list[FixtureMode]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "manufacturer": self.manufacturer,
            "name": self.name,
            "modes": [mode.to_dict() for mode in self.modes],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FixtureProfile":
        return cls(
            id=str(data["id"]),
            manufacturer=str(data["manufacturer"]),
            name=str(data["name"]),
            modes=[FixtureMode.from_dict(mode) for mode in data.get("modes", [])],
        )


@dataclass
class PatchEntry:
    id: str
    fixture_profile_id: str
    mode_index: int
    universe: int
    start_address: int
    label: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fixture_profile_id": self.fixture_profile_id,
            "mode_index": self.mode_index,
            "universe": self.universe,
            "start_address": self.start_address,
            "label": self.label,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PatchEntry":
        return cls(
            id=str(data["id"]),
            fixture_profile_id=str(data["fixture_profile_id"]),
            mode_index=int(data["mode_index"]),
            universe=int(data["universe"]),
            start_address=int(data["start_address"]),
            label=str(data["label"]),
        )
