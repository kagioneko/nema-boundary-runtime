from __future__ import annotations
from enum import Enum
from typing import Annotated, Any
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictStr

UnitFloat = Annotated[StrictFloat, Field(ge=0, le=1)]
ShortText = Annotated[StrictStr, Field(max_length=2000)]

class SupportEscalation(str, Enum):
    none = "none"
    possible = "possible"
    high = "high"

class ControlState(BaseModel):
    model_config = ConfigDict(extra="forbid")
    arousal: UnitFloat
    distress: UnitFloat
    decision_dependency: UnitFloat
    emotional_intensity: UnitFloat
    uncertainty: UnitFloat
    urgency: UnitFloat
    exclusive_attachment: UnitFloat
    support_escalation: SupportEscalation = SupportEscalation.none
    evidence: dict[Annotated[str, Field(max_length=64)], Annotated[str, Field(max_length=500)]] = Field(default_factory=dict, max_length=16)

class AnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: StrictStr = Field(min_length=1, max_length=8000)
    history: list[ShortText] = Field(default_factory=list, max_length=12)
    state_override: ControlState | None = None

class ConditionTrace(BaseModel):
    field: str
    observed: Any
    op: str
    expected: Any
    matched: bool

class PolicyTrace(BaseModel):
    policy_id: str
    priority: int
    fired: bool
    conditions: list[ConditionTrace]
    directives: list[str]

class AnalysisResult(BaseModel):
    profile_id: str
    policy_version: str
    inference_mode: str
    state: ControlState
    fired_policies: list[str]
    directives: list[str]
    trace: list[PolicyTrace]
    baseline_response: str
    controlled_response: str
    change_reasons: list[str]
