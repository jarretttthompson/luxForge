"""MappingEngine: evaluates mapping rules against audio analysis to produce output values."""

from src.audio.types import AnalysisResult
from src.mapping.parameters import ParameterRegistry
from src.mapping.transforms import build_transform_chain
from src.mapping.types import MappingRule, OutputValue


class MappingEngine:
    """Evaluates enabled mapping rules against an AnalysisResult each frame.

    Transform chains are built once per rule (on add_rule) and cached so that
    stateful transforms (e.g. Smooth, Pulse) persist state across evaluations.
    """

    def __init__(self, registry: ParameterRegistry) -> None:
        self._registry = registry
        self._rules: dict[str, MappingRule] = {}
        self._chains: dict[str, list] = {}

    def add_rule(self, rule: MappingRule) -> None:
        """Register a rule and build its transform chain."""
        self._rules[rule.id] = rule
        self._chains[rule.id] = build_transform_chain(rule.transform_chain)

    def remove_rule(self, rule_id: str) -> None:
        """Remove a rule and discard its cached transform chain."""
        self._rules.pop(rule_id, None)
        self._chains.pop(rule_id, None)

    def enable_rule(self, rule_id: str) -> None:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = True

    def disable_rule(self, rule_id: str) -> None:
        if rule_id in self._rules:
            self._rules[rule_id].enabled = False

    def get_rules(self) -> list[MappingRule]:
        return list(self._rules.values())

    def evaluate(self, analysis: AnalysisResult, dt: float) -> list[OutputValue]:
        """Evaluate all enabled rules and return the resulting output values.

        Args:
            analysis: Current audio analysis result.
            dt: Seconds elapsed since the previous evaluation call.
        """
        outputs: list[OutputValue] = []
        for rule in self._rules.values():
            if not rule.enabled:
                continue

            value = ParameterRegistry.resolve_input(rule.input_param, analysis)

            chain = self._chains.get(rule.id)
            if chain is None:
                chain = build_transform_chain(rule.transform_chain)
                self._chains[rule.id] = chain

            for transform in chain:
                value = transform(value, dt)

            outputs.append(OutputValue(target=rule.output_param, value=value))

        return outputs
