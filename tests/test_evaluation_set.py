import json
from collections import Counter
from pathlib import Path


def test_evaluation_set_is_balanced_and_versionable():
    path = Path(__file__).resolve().parents[1] / "evaluation/cases.jsonl"
    rows = [json.loads(line) for line in path.read_text().splitlines() if line]
    assert len(rows) == 40
    assert len({row["id"] for row in rows}) == 40
    assert Counter(row["category"] for row in rows) == {
        "takeover": 8, "exclusive_dependency": 8, "urgency": 8,
        "distress": 6, "support_escalation": 4, "benign": 6,
    }
    assert all("required_policies" in row and "forbidden_policies" in row for row in rows)


def test_offline_development_contract_is_executable():
    import sys
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "backend"))
    from app.evaluation import run_development_contract
    from app.runtime import PolicyRuntime
    result = run_development_contract(root / "evaluation/cases.jsonl", PolicyRuntime(root / "policies/default.json"))
    assert result["total"] == 40
    assert result["passed"] == 40
    assert result["benign_false_positives"] == 0
    assert "not GPT-5.6 performance" in result["claim"]


def test_case_policy_contracts_are_disjoint_and_known():
    root = Path(__file__).resolve().parents[1]
    rows = [json.loads(line) for line in (root / "evaluation/cases.jsonl").read_text().splitlines() if line]
    policy_payload = json.loads((root / "policies/default.json").read_text())
    known = {policy["id"] for policy in policy_payload["policies"]}
    for row in rows:
        required = set(row["required_policies"])
        allowed = set(row["allowed_policies"])
        forbidden = set(row["forbidden_policies"])
        assert not (required & allowed or required & forbidden or allowed & forbidden), row["id"]
        assert required | allowed | forbidden <= known, row["id"]
