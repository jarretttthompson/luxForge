"""Scene and preset data models."""

from dataclasses import dataclass, field
from typing import Any

from src.console.types import ConsoleCommand, ConsoleCapability
from src.mapping.types import MappingRule


@dataclass
class Scene:
    """A named collection of mapping rules and cuelist triggers.

    Activating a scene loads its mapping rules into the engine and
    fires any cuelist triggers (e.g., go on playback 1).
    """
    id: str
    name: str
    description: str = ""
    mapping_rules: list[MappingRule] = field(default_factory=list)
    cuelist_triggers: list[ConsoleCommand] = field(default_factory=list)
    transition_time_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "mapping_rules": [r.to_dict() for r in self.mapping_rules],
            "cuelist_triggers": [
                {
                    "target": c.target,
                    "value": c.value,
                    "command_type": c.command_type.value,
                }
                for c in self.cuelist_triggers
            ],
            "transition_time_ms": self.transition_time_ms,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Scene":
        mapping_rules = [
            MappingRule.from_dict(r) for r in data.get("mapping_rules", [])
        ]
        cuelist_triggers = [
            ConsoleCommand(
                target=c["target"],
                value=c["value"],
                command_type=ConsoleCapability(c["command_type"]),
            )
            for c in data.get("cuelist_triggers", [])
        ]
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            mapping_rules=mapping_rules,
            cuelist_triggers=cuelist_triggers,
            transition_time_ms=data.get("transition_time_ms", 0),
        )


@dataclass
class Preset:
    """A reusable transform chain template."""
    id: str
    name: str
    transform_chain: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "transform_chain": self.transform_chain,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Preset":
        return cls(
            id=data["id"],
            name=data["name"],
            transform_chain=data.get("transform_chain", []),
        )
