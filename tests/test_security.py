import json
from pathlib import Path
import sys
import pytest
from pydantic import ValidationError
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.main import app
from app.models import AnalyzeRequest, ControlState
from app.runtime import PolicyBundle
from fastapi.testclient import TestClient


def test_strict_state_rejects_coercion_and_extras():
    base = dict(arousal=.2, distress=.2, decision_dependency=.2, emotional_intensity=.2, uncertainty=.2, urgency=.2, exclusive_attachment=.2)
    with pytest.raises(ValidationError):
        ControlState(**(base | {"arousal": True}))
    with pytest.raises(ValidationError):
        ControlState(**(base | {"unknown": 1}))


def test_policy_bundle_rejects_empty_unknown_and_duplicate():
    valid = json.loads((ROOT / "policies/default.json").read_text())
    bad_group = {"version":"x", "policies":[{"id":"bad.one", "priority":1, "when":{"all":[]}, "then":["require_caution"]}]}
    with pytest.raises(ValidationError):
        PolicyBundle.model_validate(bad_group, strict=True)
    duplicate = valid | {"policies": [valid["policies"][0], valid["policies"][0]]}
    with pytest.raises(ValidationError):
        PolicyBundle.model_validate(duplicate, strict=True)


def test_request_limits_and_security_headers():
    client = TestClient(app)
    too_large = client.post("/api/analyze", content=b"x" * 65537, headers={"content-type":"application/json"})
    assert too_large.status_code == 413
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_history_item_and_extra_request_are_rejected():
    with pytest.raises(ValidationError):
        AnalyzeRequest(text="ok", history=["x" * 2001])
    with pytest.raises(ValidationError):
        AnalyzeRequest(text="ok", extra_field=True)

def test_short_history_participates_in_offline_inference():
    client = TestClient(app)
    response = client.post("/api/analyze", json={"text":"どう思う？", "history":["全部あなたが決めて。自分では決められない。"]})
    assert response.status_code == 200
    assert "autonomy.restore" in response.json()["fired_policies"]

@pytest.mark.parametrize("condition", [
    {"field":"support_escalation", "op":">", "value":0.5},
    {"field":"distress", "op":">", "value":"high"},
])
def test_condition_field_value_types_are_compatible(condition):
    payload = {"version":"x", "policies":[{"id":"bad.type", "priority":1, "when":{"all":[condition]}, "then":["require_caution"]}]}
    with pytest.raises(ValidationError):
        PolicyBundle.model_validate(payload, strict=True)


def test_chunked_body_limit_cannot_be_bypassed():
    client = TestClient(app)
    valid = b'{"text":"ok"}'
    def chunks():
        yield valid[:-1]
        yield b' ' * 65537
        yield valid[-1:]
    response = client.post("/api/analyze", content=chunks(), headers={"content-type":"application/json"})
    assert response.status_code == 413
    assert response.headers["x-content-type-options"] == "nosniff"


def test_false_small_content_length_cannot_bypass_actual_limit():
    client = TestClient(app)
    valid = b'{"text":"ok"}'
    def chunks():
        yield valid[:-1]
        yield b' ' * 65537
        yield valid[-1:]
    response = client.post("/api/analyze", content=chunks(), headers={"content-type":"application/json", "content-length":"1"})
    assert response.status_code == 413


def test_evaluation_endpoint_is_labeled_as_offline_fixture():
    response = TestClient(app).get("/api/evaluation")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 40
    assert payload["mode"] == "offline_demo_fixture"
    assert "not GPT-5.6 performance" in payload["claim"]


def test_numeric_policy_threshold_accepts_integer_boundaries():
    payload = {"version":"x", "policies":[{"id":"edge.one", "priority":1, "when":{"all":[{"field":"distress", "op":">=", "value":1}]}, "then":["require_caution"]}]}
    assert PolicyBundle.model_validate(payload, strict=True).policies[0].when.all[0].value == 1


def test_policy_replay_changes_threshold_without_persistence():
    client = TestClient(app)
    original = client.get('/api/policies').json()
    policy = next(p for p in original['policies'] if p['id'] == 'autonomy.restore')
    policy['when']['all'][0]['value'] = 0.95
    response = client.post('/api/replay', json={'text':'全部あなたが決めて。', 'policy_bundle':original})
    assert response.status_code == 200
    assert 'autonomy.restore' not in response.json()['fired_policies']
    persisted = client.get('/api/policies').json()
    assert next(p for p in persisted['policies'] if p['id']=='autonomy.restore')['when']['all'][0]['value'] == 0.65


def test_policy_replay_rejects_unknown_directive():
    client = TestClient(app)
    bundle = client.get('/api/policies').json()
    bundle['policies'][0]['then'] = ['do_anything']
    assert client.post('/api/replay', json={'text':'test', 'policy_bundle':bundle}).status_code == 422


def test_policy_bundle_size_limits():
    condition = {"field":"distress", "op":">", "value":0.5}
    too_many_conditions = {"version":"x", "policies":[{"id":"too.many.conditions", "priority":1, "when":{"all":[condition]*17}, "then":["require_caution"]}]}
    with pytest.raises(ValidationError):
        PolicyBundle.model_validate(too_many_conditions, strict=True)
    policies = [{"id":f"policy.{i}", "priority":i, "when":{"all":[condition]}, "then":["require_caution"]} for i in range(65)]
    with pytest.raises(ValidationError):
        PolicyBundle.model_validate({"version":"x", "policies":policies}, strict=True)


def test_readiness_and_version_are_explicitly_offline():
    client = TestClient(app)
    assert client.get('/ready').json() == {'status':'ready','inference_mode':'offline_demo_fixture'}
    version = client.get('/version').json()
    assert version['app_version'] == '0.1.0'
    assert version['inference_mode'] == 'offline_demo_fixture'
    assert len(version['policy_sha256']) == len(version['profile_sha256']) == 64
