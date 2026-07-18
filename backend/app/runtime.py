from __future__ import annotations
import operator
from pathlib import Path
from typing import Annotated, Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
from .models import ConditionTrace, ControlState, PolicyTrace

OPS = {">": operator.gt, ">=": operator.ge, "<": operator.lt, "<=": operator.le, "==": operator.eq}
StateField = Literal["arousal", "distress", "decision_dependency", "emotional_intensity", "uncertainty", "urgency", "exclusive_attachment", "support_escalation"]
Operator = Literal[">", ">=", "<", "<=", "=="]
Directive = Literal["reduce_assertiveness", "increase_reassurance", "reduce_pressure", "simplify_response", "reduce_emotional_intensity", "reduce_intervention", "return_decision_to_user", "require_confirmation", "avoid_decision_takeover", "restrict_relational_claims", "block_exclusive_language", "block_dependency_reinforcement", "require_caution", "suggest_human_support", "suggest_immediate_human_support"]

class Condition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: StateField
    op: Operator
    value: float | int | Literal["none", "possible", "high"]
    @model_validator(mode="after")
    def compatible_field_value(self):
        if self.field == "support_escalation":
            if self.op != "==" or self.value not in {"none", "possible", "high"}:
                raise ValueError("support_escalation requires == and an enum value")
        elif isinstance(self.value, bool) or not isinstance(self.value, (int, float)):
            raise ValueError("numeric state fields require a float threshold")
        return self

class ConditionGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")
    all: Annotated[list[Condition], Field(min_length=1, max_length=16)] | None = None
    any: Annotated[list[Condition], Field(min_length=1, max_length=16)] | None = None
    @model_validator(mode="after")
    def exactly_one_group(self):
        if (self.all is None) == (self.any is None):
            raise ValueError("exactly one of all or any is required")
        return self

class PolicyDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: Annotated[str, Field(pattern=r"^[a-z][a-z0-9_.-]{1,63}$")]
    priority: Annotated[int, Field(ge=0, le=1000)]
    when: ConditionGroup
    then: Annotated[list[Directive], Field(min_length=1, max_length=16)]

class PolicyBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Annotated[str, Field(min_length=1, max_length=64)]
    policies: Annotated[list[PolicyDefinition], Field(min_length=1, max_length=64)]
    @model_validator(mode="after")
    def unique_policy_ids(self):
        ids = [policy.id for policy in self.policies]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate policy id")
        return self

class PolicyRuntime:
    def __init__(self, policy_path: Path | None = None, *, bundle: PolicyBundle | None = None):
        if (policy_path is None) == (bundle is None):
            raise ValueError("provide exactly one of policy_path or bundle")
        if bundle is None:
            assert policy_path is not None
            bundle = PolicyBundle.model_validate_json(policy_path.read_text(encoding="utf-8"), strict=True)
        self.bundle = bundle
        self.version = bundle.version
        self.policies = sorted(bundle.policies, key=lambda p: (-p.priority, p.id))

    @classmethod
    def from_bundle(cls, bundle: PolicyBundle) -> "PolicyRuntime":
        return cls(bundle=bundle)
    @staticmethod
    def _value(state: ControlState, field: str) -> Any:
        value = getattr(state, field)
        return value.value if hasattr(value, "value") else value
    def evaluate(self, state: ControlState) -> tuple[list[str], list[PolicyTrace]]:
        directives: list[str] = []
        traces: list[PolicyTrace] = []
        for policy in self.policies:
            group_name = "all" if policy.when.all is not None else "any"
            conditions = policy.when.all if policy.when.all is not None else policy.when.any
            assert conditions is not None
            condition_traces, matches = [], []
            for condition in conditions:
                observed = self._value(state, condition.field)
                matched = OPS[condition.op](observed, condition.value)
                matches.append(matched)
                condition_traces.append(ConditionTrace(field=condition.field, observed=observed, op=condition.op, expected=condition.value, matched=matched))
            fired = all(matches) if group_name == "all" else any(matches)
            emitted = list(policy.then) if fired else []
            for directive in emitted:
                if directive not in directives:
                    directives.append(directive)
            traces.append(PolicyTrace(policy_id=policy.id, priority=policy.priority, fired=fired, conditions=condition_traces, directives=emitted))
        return directives, traces
