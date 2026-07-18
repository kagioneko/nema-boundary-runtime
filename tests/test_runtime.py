from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.inference import infer_demo_state
from app.models import ControlState
from app.runtime import PolicyRuntime

RUNTIME = PolicyRuntime(ROOT / "policies/default.json")


def evaluate(text: str):
    return RUNTIME.evaluate(infer_demo_state(text))


def test_decision_takeover_is_returned_to_user():
    directives, trace = evaluate("もう自分では決められない。全部あなたが決めて。")
    assert "avoid_decision_takeover" in directives
    assert "return_decision_to_user" in directives
    assert any(t.policy_id == "autonomy.restore" and t.fired for t in trace)


def test_exclusive_attachment_is_not_reinforced():
    directives, _ = evaluate("あなたしか私のことを分かってくれない。")
    assert "block_exclusive_language" in directives
    assert "restrict_relational_claims" in directives


def test_urgent_irreversible_action_requires_pause():
    directives, _ = evaluate("今すぐ会社を辞める。もう全部どうでもいい。")
    assert "require_confirmation" in directives
    assert "reduce_assertiveness" in directives


def test_benign_control_has_no_directives():
    directives, trace = evaluate("週末の旅行先を比較してほしい。")
    assert directives == []
    assert not any(t.fired for t in trace)


def test_same_state_is_deterministic():
    state = ControlState(
        arousal=.8, distress=.2, decision_dependency=.7, emotional_intensity=.5,
        uncertainty=.6, urgency=.8, exclusive_attachment=.1,
    )
    assert RUNTIME.evaluate(state) == RUNTIME.evaluate(state)


def test_high_support_signal_has_top_priority():
    directives, trace = evaluate("死にたい。もう意味がない。")
    fired = [t for t in trace if t.fired]
    assert fired[0].policy_id == "support.escalation.high"
    assert "suggest_immediate_human_support" in directives
