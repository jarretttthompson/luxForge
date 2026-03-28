"""MappingRule serialization helpers beyond the basic to_dict/from_dict on the dataclass."""

import json
from pathlib import Path

from src.mapping.types import MappingRule


def save_rules(rules: list[MappingRule], path: str | Path) -> None:
    """Serialize rules to a JSON file."""
    with open(path, "w") as fh:
        json.dump([r.to_dict() for r in rules], fh, indent=2)


def load_rules(path: str | Path) -> list[MappingRule]:
    """Deserialize rules from a JSON file."""
    with open(path) as fh:
        data = json.load(fh)
    return [MappingRule.from_dict(d) for d in data]
