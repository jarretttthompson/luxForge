"""Tests for MappingEngine: evaluate(), rule management, and transform state caching."""

import pytest

from src.audio.types import AnalysisResult
from src.mapping.engine import MappingEngine
from src.mapping.parameters import ParameterRegistry
from src.mapping.types import MappingRule, OutputValue


def make_rule(**kwargs) -> MappingRule:
    defaults: dict = {
        "id": "r1",
        "name": "Test Rule",
        "input_param": "audio.rms",
        "transform_chain": [],
        "output_param": "output.test",
        "enabled": True,
    }
    defaults.update(kwargs)
    return MappingRule(**defaults)


def make_engine() -> MappingEngine:
    return MappingEngine(ParameterRegistry())


class TestEvaluate:
    def test_empty_engine_returns_empty(self):
        eng = make_engine()
        result = eng.evaluate(AnalysisResult(), 0.016)
        assert result == []

    def test_passthrough_rule_returns_raw_value(self):
        eng = make_engine()
        eng.add_rule(make_rule(input_param="audio.rms"))
        outputs = eng.evaluate(AnalysisResult(rms=0.75), 0.016)
        assert len(outputs) == 1
        assert outputs[0].target == "output.test"
        assert outputs[0].value == pytest.approx(0.75)

    def test_output_target_matches_rule_output_param(self):
        eng = make_engine()
        eng.add_rule(make_rule(output_param="console.fader.1"))
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert outputs[0].target == "console.fader.1"

    def test_returns_output_value_instances(self):
        eng = make_engine()
        eng.add_rule(make_rule())
        outputs = eng.evaluate(AnalysisResult(), 0.016)
        assert all(isinstance(o, OutputValue) for o in outputs)

    def test_scale_transform_applied(self):
        eng = make_engine()
        eng.add_rule(make_rule(
            transform_chain=[{"type": "Scale", "min_out": 0.0, "max_out": 2.0}],
        ))
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert outputs[0].value == pytest.approx(1.0)

    def test_transform_chain_applied_in_order(self):
        # Scale 0.8 → 1.6, then Clamp → 1.0
        eng = make_engine()
        eng.add_rule(make_rule(
            transform_chain=[
                {"type": "Scale", "min_out": 0.0, "max_out": 2.0},
                {"type": "Clamp", "lo": 0.0, "hi": 1.0},
            ],
        ))
        outputs = eng.evaluate(AnalysisResult(rms=0.8), 0.016)
        assert outputs[0].value == pytest.approx(1.0)

    def test_multiple_rules_all_evaluated(self):
        eng = make_engine()
        eng.add_rule(make_rule(id="r1", output_param="out.a", input_param="audio.rms"))
        eng.add_rule(make_rule(id="r2", output_param="out.b", input_param="audio.peak"))
        outputs = eng.evaluate(AnalysisResult(rms=0.3, peak=0.8), 0.016)
        assert len(outputs) == 2
        by_target = {o.target: o.value for o in outputs}
        assert by_target["out.a"] == pytest.approx(0.3)
        assert by_target["out.b"] == pytest.approx(0.8)

    def test_band_energy_input(self):
        from src.audio.types import BandEnergies
        eng = make_engine()
        eng.add_rule(make_rule(input_param="audio.band.sub"))
        from src.audio.types import AnalysisResult as AR
        outputs = eng.evaluate(AR(band_energies=BandEnergies(sub=0.6)), 0.016)
        assert outputs[0].value == pytest.approx(0.6)

    def test_unknown_input_param_returns_zero(self):
        eng = make_engine()
        eng.add_rule(make_rule(input_param="audio.nonexistent"))
        outputs = eng.evaluate(AnalysisResult(), 0.016)
        assert outputs[0].value == pytest.approx(0.0)

    def test_transform_chain_state_persists_across_calls(self):
        """Smooth transform caches its state; value should move toward target over calls."""
        eng = make_engine()
        eng.add_rule(make_rule(
            transform_chain=[{"type": "Smooth", "attack": 0.1, "release": 0.5}],
        ))
        analysis = AnalysisResult(rms=1.0)
        v1 = eng.evaluate(analysis, 0.1)[0].value
        v2 = eng.evaluate(analysis, 0.1)[0].value
        v3 = eng.evaluate(analysis, 0.1)[0].value
        assert v1 < v2 < v3  # converging toward 1.0


class TestAddRemoveRules:
    def test_add_rule_appears_in_get_rules(self):
        eng = make_engine()
        rule = make_rule()
        eng.add_rule(rule)
        assert rule in eng.get_rules()

    def test_add_multiple_rules(self):
        eng = make_engine()
        eng.add_rule(make_rule(id="r1"))
        eng.add_rule(make_rule(id="r2"))
        assert len(eng.get_rules()) == 2

    def test_remove_rule_removes_from_rules(self):
        eng = make_engine()
        eng.add_rule(make_rule())
        eng.remove_rule("r1")
        assert eng.get_rules() == []

    def test_remove_rule_removes_from_evaluation(self):
        eng = make_engine()
        eng.add_rule(make_rule())
        eng.remove_rule("r1")
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert outputs == []

    def test_remove_nonexistent_rule_no_error(self):
        eng = make_engine()
        eng.remove_rule("does-not-exist")  # must not raise

    def test_remove_clears_cached_chain(self):
        """After removing a rule, its cached chain is also gone."""
        eng = make_engine()
        eng.add_rule(make_rule())
        eng.remove_rule("r1")
        assert "r1" not in eng._chains


class TestEnableDisableRules:
    def test_disabled_rule_not_in_output(self):
        eng = make_engine()
        eng.add_rule(make_rule())
        eng.disable_rule("r1")
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert outputs == []

    def test_re_enabled_rule_appears_in_output(self):
        eng = make_engine()
        eng.add_rule(make_rule())
        eng.disable_rule("r1")
        eng.enable_rule("r1")
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert len(outputs) == 1

    def test_add_disabled_rule_not_evaluated(self):
        eng = make_engine()
        eng.add_rule(make_rule(enabled=False))
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert outputs == []

    def test_enable_nonexistent_rule_no_error(self):
        eng = make_engine()
        eng.enable_rule("does-not-exist")

    def test_disable_nonexistent_rule_no_error(self):
        eng = make_engine()
        eng.disable_rule("does-not-exist")

    def test_disable_only_affects_targeted_rule(self):
        eng = make_engine()
        eng.add_rule(make_rule(id="r1", output_param="out.a"))
        eng.add_rule(make_rule(id="r2", output_param="out.b"))
        eng.disable_rule("r1")
        outputs = eng.evaluate(AnalysisResult(rms=0.5), 0.016)
        assert len(outputs) == 1
        assert outputs[0].target == "out.b"


class TestGetRules:
    def test_initially_empty(self):
        eng = make_engine()
        assert eng.get_rules() == []

    def test_returns_list_copy(self):
        """Mutating the returned list must not affect the engine."""
        eng = make_engine()
        eng.add_rule(make_rule())
        rules = eng.get_rules()
        rules.clear()
        assert len(eng.get_rules()) == 1
