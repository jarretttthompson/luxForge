"""Mapping engine types: rules, output values."""

from dataclasses import dataclass, field
from typing import Any

from src.console.types import ConsoleCommand, ConsoleCapability


@dataclass
class MappingRule:
    """A user-defined rule mapping an audio parameter to a lighting parameter.

    input_param: dotted path like "audio.band.sub" or "audio.bpm"
    transform_chain: list of transform dicts (serialized form), e.g. [{"type": "Smooth", "attack": 0.1, "release": 0.4}]
    output_param: dotted path like "onyx.playback.1.fader"
    condition: optional expression string, e.g. "audio.bpm > 100"
    """
    id: str
    name: str
    input_param: str
    transform_chain: list[dict[str, Any]] = field(default_factory=list)
    output_param: str = ""
    condition: str | None = None
    enabled: bool = True

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "input_param": self.input_param,
            "transform_chain": self.transform_chain,
            "output_param": self.output_param,
            "condition": self.condition,
            "enabled": self.enabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MappingRule":
        return cls(
            id=data["id"],
            name=data["name"],
            input_param=data["input_param"],
            transform_chain=data.get("transform_chain", []),
            output_param=data.get("output_param", ""),
            condition=data.get("condition"),
            enabled=data.get("enabled", True),
        )


@dataclass
class OutputValue:
    """Result of evaluating a mapping rule: a value to send to a console."""
    target: str          # output parameter name
    value: float         # computed value
    console_command: ConsoleCommand | None = None
