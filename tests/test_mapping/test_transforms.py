"""Unit tests for all transform classes."""

import pytest

from src.mapping.transforms import (
    TRANSFORM_REGISTRY,
    Clamp,
    Curve,
    Invert,
    MapRange,
    Pulse,
    Scale,
    Smooth,
    Threshold,
    build_transform_chain,
)


class TestSmooth:
    def test_attack_moves_toward_input(self):
        s = Smooth(attack=0.1, release=0.4)
        # dt=0.1, attack=0.1 → alpha = 1 − exp(−1) ≈ 0.632
        result = s(1.0, 0.1)
        assert 0.5 < result < 0.8

    def test_attack_vs_release_speed(self):
        """Release at 0.5s should be slower than release at 0.1s."""
        slow = Smooth(attack=0.1, release=0.5)
        fast = Smooth(attack=0.1, release=0.1)

        # Saturate both smoothers at 1.0
        for _ in range(50):
            slow(1.0, 0.1)
            fast(1.0, 0.1)

        # One step releasing toward 0
        r_slow = slow(0.0, 0.1)
        r_fast = fast(0.0, 0.1)

        # fast drops more: its value is closer to 0
        assert r_fast < r_slow

    def test_attack_faster_than_release(self):
        """Input rising: attack path used; attack=0.01 should converge faster than release=0.5."""
        fast_attack = Smooth(attack=0.01, release=0.5)
        slow_attack = Smooth(attack=0.5, release=0.01)

        r_fast = fast_attack(1.0, 0.1)
        r_slow = slow_attack(1.0, 0.1)

        assert r_fast > r_slow

    def test_zero_rate_snaps_instantly(self):
        s = Smooth(attack=0.0, release=0.0)
        assert s(0.7, 0.1) == pytest.approx(0.7)
        assert s(0.3, 0.1) == pytest.approx(0.3)

    def test_converges_to_steady_state(self):
        s = Smooth(attack=0.05, release=0.05)
        for _ in range(200):
            s(1.0, 0.05)
        assert s._current == pytest.approx(1.0, abs=1e-3)

    def test_serialization_roundtrip(self):
        s = Smooth(attack=0.1, release=0.4)
        d = s.to_dict()
        assert d == {"type": "Smooth", "attack": 0.1, "release": 0.4}
        s2 = Smooth.from_dict(d)
        assert s2.attack == 0.1
        assert s2.release == 0.4


class TestScale:
    def test_zero_maps_to_min(self):
        s = Scale(min_out=0.2, max_out=0.8)
        assert s(0.0, 0.0) == pytest.approx(0.2)

    def test_one_maps_to_max(self):
        s = Scale(min_out=0.2, max_out=0.8)
        assert s(1.0, 0.0) == pytest.approx(0.8)

    def test_midpoint(self):
        s = Scale(min_out=0.0, max_out=1.0)
        assert s(0.5, 0.0) == pytest.approx(0.5)

    def test_negative_range(self):
        s = Scale(min_out=-1.0, max_out=0.0)
        assert s(0.5, 0.0) == pytest.approx(-0.5)

    def test_larger_range(self):
        s = Scale(min_out=0.0, max_out=255.0)
        assert s(0.5, 0.0) == pytest.approx(127.5)

    def test_serialization_roundtrip(self):
        s = Scale(min_out=0.2, max_out=0.8)
        d = s.to_dict()
        assert d["type"] == "Scale"
        s2 = Scale.from_dict(d)
        assert s2.min_out == 0.2
        assert s2.max_out == 0.8


class TestThreshold:
    def test_above_returns_above_val(self):
        t = Threshold(level=0.5)
        assert t(0.6, 0.0) == pytest.approx(1.0)

    def test_below_returns_below_val(self):
        t = Threshold(level=0.5)
        assert t(0.4, 0.0) == pytest.approx(0.0)

    def test_at_level_returns_above_val(self):
        t = Threshold(level=0.5)
        assert t(0.5, 0.0) == pytest.approx(1.0)

    def test_custom_values(self):
        t = Threshold(level=0.3, above_val=0.8, below_val=0.2)
        assert t(0.5, 0.0) == pytest.approx(0.8)
        assert t(0.1, 0.0) == pytest.approx(0.2)

    def test_serialization_roundtrip(self):
        t = Threshold(level=0.5, above_val=0.9, below_val=0.1)
        d = t.to_dict()
        t2 = Threshold.from_dict(d)
        assert t2.level == 0.5
        assert t2.above_val == 0.9
        assert t2.below_val == 0.1

    def test_defaults_from_dict(self):
        t = Threshold.from_dict({"type": "Threshold", "level": 0.5})
        assert t.above_val == 1.0
        assert t.below_val == 0.0


class TestCurve:
    def test_square_curve(self):
        c = Curve(exponent=2.0)
        assert c(0.5, 0.0) == pytest.approx(0.25)

    def test_sqrt_curve(self):
        c = Curve(exponent=0.5)
        assert c(0.25, 0.0) == pytest.approx(0.5)

    def test_linear_exponent_one(self):
        c = Curve(exponent=1.0)
        assert c(0.7, 0.0) == pytest.approx(0.7)

    def test_zero_input(self):
        c = Curve(exponent=3.0)
        assert c(0.0, 0.0) == pytest.approx(0.0)

    def test_one_input(self):
        c = Curve(exponent=3.0)
        assert c(1.0, 0.0) == pytest.approx(1.0)

    def test_serialization_roundtrip(self):
        c = Curve(exponent=2.0)
        d = c.to_dict()
        c2 = Curve.from_dict(d)
        assert c2.exponent == 2.0


class TestInvert:
    def test_invert_zero(self):
        i = Invert()
        assert i(0.0, 0.0) == pytest.approx(1.0)

    def test_invert_one(self):
        i = Invert()
        assert i(1.0, 0.0) == pytest.approx(0.0)

    def test_invert_midpoint(self):
        i = Invert()
        assert i(0.5, 0.0) == pytest.approx(0.5)

    def test_invert_arbitrary(self):
        i = Invert()
        assert i(0.3, 0.0) == pytest.approx(0.7)

    def test_serialization_roundtrip(self):
        i = Invert()
        d = i.to_dict()
        assert d == {"type": "Invert"}
        i2 = Invert.from_dict(d)
        assert isinstance(i2, Invert)


class TestPulse:
    def test_no_output_before_rising_edge(self):
        p = Pulse(duration_ms=100.0)
        assert p(0.0, 0.01) == pytest.approx(0.0)

    def test_rising_edge_triggers_pulse(self):
        p = Pulse(duration_ms=100.0)
        p(0.0, 0.01)           # below threshold
        result = p(1.0, 0.01)  # rising edge
        assert result == pytest.approx(1.0)

    def test_pulse_expires_after_duration(self):
        p = Pulse(duration_ms=50.0)
        p(0.0, 0.0)
        p(1.0, 0.01)    # trigger: remaining = 50 − 10 = 40 ms → 1.0
        result = p(1.0, 0.05)  # remaining = 40 − 50 = −10 ms → 0.0
        assert result == pytest.approx(0.0)

    def test_no_pulse_on_sustained_high(self):
        p = Pulse(duration_ms=10.0)
        p(0.0, 0.0)
        p(1.0, 0.001)   # trigger; remaining = 10 − 1 = 9 ms
        p(1.0, 0.02)    # remaining = 9 − 20 = −11 → expires
        result = p(1.0, 0.01)  # sustained high, no new edge
        assert result == pytest.approx(0.0)

    def test_no_pulse_on_falling_edge(self):
        p = Pulse(duration_ms=100.0)
        p(0.0, 0.0)
        p(1.0, 0.001)  # trigger
        p(1.0, 0.2)    # pulse expires
        result = p(0.0, 0.01)  # falling edge — should not retrigger
        assert result == pytest.approx(0.0)

    def test_retriggerable_on_new_rising_edge(self):
        p = Pulse(duration_ms=20.0)
        p(0.0, 0.0)
        p(1.0, 0.001)  # first trigger
        p(1.0, 0.03)   # expire
        p(0.0, 0.01)   # fall
        result = p(1.0, 0.001)  # second rising edge
        assert result == pytest.approx(1.0)

    def test_serialization_roundtrip(self):
        p = Pulse(duration_ms=100.0)
        d = p.to_dict()
        assert d == {"type": "Pulse", "duration_ms": 100.0}
        p2 = Pulse.from_dict(d)
        assert p2.duration_ms == 100.0


class TestMapRange:
    def test_basic_remap(self):
        m = MapRange(in_lo=0.0, in_hi=1.0, out_lo=0.0, out_hi=100.0)
        assert m(0.5, 0.0) == pytest.approx(50.0)

    def test_clamps_below_in_lo(self):
        m = MapRange(in_lo=0.2, in_hi=0.8, out_lo=0.0, out_hi=1.0)
        assert m(0.0, 0.0) == pytest.approx(0.0)

    def test_clamps_above_in_hi(self):
        m = MapRange(in_lo=0.2, in_hi=0.8, out_lo=0.0, out_hi=1.0)
        assert m(1.0, 0.0) == pytest.approx(1.0)

    def test_inverted_output_range(self):
        m = MapRange(in_lo=0.0, in_hi=1.0, out_lo=1.0, out_hi=0.0)
        assert m(0.25, 0.0) == pytest.approx(0.75)

    def test_quarter_point(self):
        m = MapRange(in_lo=0.0, in_hi=1.0, out_lo=0.0, out_hi=100.0)
        assert m(0.25, 0.0) == pytest.approx(25.0)

    def test_degenerate_same_in_lo_in_hi(self):
        m = MapRange(in_lo=0.5, in_hi=0.5, out_lo=0.3, out_hi=0.7)
        assert m(0.5, 0.0) == pytest.approx(0.3)

    def test_serialization_roundtrip(self):
        m = MapRange(in_lo=0.2, in_hi=0.8, out_lo=10.0, out_hi=90.0)
        d = m.to_dict()
        m2 = MapRange.from_dict(d)
        assert m2.in_lo == 0.2
        assert m2.in_hi == 0.8
        assert m2.out_lo == 10.0
        assert m2.out_hi == 90.0


class TestClamp:
    def test_clamp_below_lo(self):
        c = Clamp(lo=0.2, hi=0.8)
        assert c(-0.5, 0.0) == pytest.approx(0.2)

    def test_clamp_above_hi(self):
        c = Clamp(lo=0.2, hi=0.8)
        assert c(1.5, 0.0) == pytest.approx(0.8)

    def test_within_range_unchanged(self):
        c = Clamp(lo=0.2, hi=0.8)
        assert c(0.5, 0.0) == pytest.approx(0.5)

    def test_exact_lo_boundary(self):
        c = Clamp(lo=0.0, hi=1.0)
        assert c(0.0, 0.0) == pytest.approx(0.0)

    def test_exact_hi_boundary(self):
        c = Clamp(lo=0.0, hi=1.0)
        assert c(1.0, 0.0) == pytest.approx(1.0)

    def test_serialization_roundtrip(self):
        c = Clamp(lo=0.1, hi=0.9)
        d = c.to_dict()
        assert d == {"type": "Clamp", "lo": 0.1, "hi": 0.9}
        c2 = Clamp.from_dict(d)
        assert c2.lo == 0.1
        assert c2.hi == 0.9


class TestTransformRegistry:
    def test_all_types_registered(self):
        expected = {"Smooth", "Scale", "Threshold", "Curve", "Invert", "Pulse", "MapRange", "Clamp"}
        assert expected == set(TRANSFORM_REGISTRY.keys())

    def test_registry_maps_to_correct_classes(self):
        assert TRANSFORM_REGISTRY["Smooth"] is Smooth
        assert TRANSFORM_REGISTRY["Scale"] is Scale
        assert TRANSFORM_REGISTRY["Invert"] is Invert


class TestBuildTransformChain:
    def test_empty_chain(self):
        chain = build_transform_chain([])
        assert chain == []

    def test_single_transform(self):
        chain = build_transform_chain([{"type": "Invert"}])
        assert len(chain) == 1
        assert isinstance(chain[0], Invert)

    def test_multiple_transforms(self):
        chain = build_transform_chain([
            {"type": "Scale", "min_out": 0.0, "max_out": 2.0},
            {"type": "Clamp", "lo": 0.0, "hi": 1.0},
        ])
        assert len(chain) == 2
        assert isinstance(chain[0], Scale)
        assert isinstance(chain[1], Clamp)

    def test_unknown_type_raises(self):
        with pytest.raises(ValueError, match="Unknown transform type"):
            build_transform_chain([{"type": "DoesNotExist"}])

    def test_chain_applies_in_order(self):
        # Scale [0,1]→[0,2] then Clamp [0,1]: value 0.8 → 1.6 → 1.0
        chain = build_transform_chain([
            {"type": "Scale", "min_out": 0.0, "max_out": 2.0},
            {"type": "Clamp", "lo": 0.0, "hi": 1.0},
        ])
        value = 0.8
        for t in chain:
            value = t(value, 0.016)
        assert value == pytest.approx(1.0)

    def test_stateful_transforms_maintain_state(self):
        """Smooth instance in a built chain must retain state across calls."""
        chain = build_transform_chain([{"type": "Smooth", "attack": 0.1, "release": 0.5}])
        v1 = chain[0](1.0, 0.1)
        v2 = chain[0](1.0, 0.1)
        # Both calls approach 1.0; v2 is closer than v1
        assert v2 > v1
