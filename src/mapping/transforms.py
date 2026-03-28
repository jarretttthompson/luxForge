"""Transform classes for the audio-to-lighting mapping pipeline."""

from __future__ import annotations

import math
from typing import Any


class Smooth:
    """Asymmetric exponential envelope follower.

    When input > current, move toward input at attack rate (seconds to ~63%).
    When input < current, move at release rate.
    """

    def __init__(self, attack: float, release: float) -> None:
        self.attack = attack
        self.release = release
        self._current: float = 0.0

    def __call__(self, value: float, dt: float) -> float:
        rate = self.attack if value > self._current else self.release
        if rate <= 0.0:
            self._current = value
        else:
            alpha = 1.0 - math.exp(-dt / rate)
            self._current += alpha * (value - self._current)
        return self._current

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Smooth", "attack": self.attack, "release": self.release}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Smooth:
        return cls(attack=data["attack"], release=data["release"])


class Scale:
    """Linear map from [0, 1] to [min_out, max_out]."""

    def __init__(self, min_out: float, max_out: float) -> None:
        self.min_out = min_out
        self.max_out = max_out

    def __call__(self, value: float, dt: float) -> float:
        return self.min_out + value * (self.max_out - self.min_out)

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Scale", "min_out": self.min_out, "max_out": self.max_out}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scale:
        return cls(min_out=data["min_out"], max_out=data["max_out"])


class Threshold:
    """Binary gate: returns above_val when value >= level, else below_val."""

    def __init__(
        self,
        level: float,
        above_val: float = 1.0,
        below_val: float = 0.0,
    ) -> None:
        self.level = level
        self.above_val = above_val
        self.below_val = below_val

    def __call__(self, value: float, dt: float) -> float:
        return self.above_val if value >= self.level else self.below_val

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "Threshold",
            "level": self.level,
            "above_val": self.above_val,
            "below_val": self.below_val,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Threshold:
        return cls(
            level=data["level"],
            above_val=data.get("above_val", 1.0),
            below_val=data.get("below_val", 0.0),
        )


class Curve:
    """Power curve (value ** exponent) for gamma correction."""

    def __init__(self, exponent: float) -> None:
        self.exponent = exponent

    def __call__(self, value: float, dt: float) -> float:
        return value**self.exponent

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Curve", "exponent": self.exponent}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Curve:
        return cls(exponent=data["exponent"])


class Invert:
    """Returns 1.0 - value."""

    def __call__(self, value: float, dt: float) -> float:
        return 1.0 - value

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Invert"}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Invert:
        return cls()


class Pulse:
    """On rising edge (value crosses 0.5 upward), output 1.0 for duration_ms, then 0.0."""

    def __init__(self, duration_ms: float) -> None:
        self.duration_ms = duration_ms
        self._prev: float = 0.0
        self._remaining_ms: float = 0.0

    def __call__(self, value: float, dt: float) -> float:
        if self._prev < 0.5 and value >= 0.5:
            self._remaining_ms = self.duration_ms
        self._prev = value
        if self._remaining_ms > 0.0:
            self._remaining_ms -= dt * 1000.0
            if self._remaining_ms > 0.0:
                return 1.0
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Pulse", "duration_ms": self.duration_ms}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pulse:
        return cls(duration_ms=data["duration_ms"])


class MapRange:
    """General linear remap from [in_lo, in_hi] to [out_lo, out_hi] with clamping."""

    def __init__(
        self,
        in_lo: float,
        in_hi: float,
        out_lo: float,
        out_hi: float,
    ) -> None:
        self.in_lo = in_lo
        self.in_hi = in_hi
        self.out_lo = out_lo
        self.out_hi = out_hi

    def __call__(self, value: float, dt: float) -> float:
        value = max(self.in_lo, min(self.in_hi, value))
        if self.in_hi == self.in_lo:
            t = 0.0
        else:
            t = (value - self.in_lo) / (self.in_hi - self.in_lo)
        return self.out_lo + t * (self.out_hi - self.out_lo)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "MapRange",
            "in_lo": self.in_lo,
            "in_hi": self.in_hi,
            "out_lo": self.out_lo,
            "out_hi": self.out_hi,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MapRange:
        return cls(
            in_lo=data["in_lo"],
            in_hi=data["in_hi"],
            out_lo=data["out_lo"],
            out_hi=data["out_hi"],
        )


class Clamp:
    """Hard limit: clamps value to [lo, hi]."""

    def __init__(self, lo: float, hi: float) -> None:
        self.lo = lo
        self.hi = hi

    def __call__(self, value: float, dt: float) -> float:
        return max(self.lo, min(self.hi, value))

    def to_dict(self) -> dict[str, Any]:
        return {"type": "Clamp", "lo": self.lo, "hi": self.hi}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Clamp:
        return cls(lo=data["lo"], hi=data["hi"])


TRANSFORM_REGISTRY: dict[str, type] = {
    "Smooth": Smooth,
    "Scale": Scale,
    "Threshold": Threshold,
    "Curve": Curve,
    "Invert": Invert,
    "Pulse": Pulse,
    "MapRange": MapRange,
    "Clamp": Clamp,
}


def build_transform_chain(chain_data: list[dict[str, Any]]) -> list:
    """Deserialize a list of transform dicts into callable transform instances."""
    chain = []
    for item in chain_data:
        type_name = item.get("type", "")
        cls = TRANSFORM_REGISTRY.get(type_name)
        if cls is None:
            raise ValueError(f"Unknown transform type: {type_name!r}")
        chain.append(cls.from_dict(item))
    return chain
