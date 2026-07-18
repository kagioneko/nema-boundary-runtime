from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from typing import Any
from .inference import infer_demo_state
from .runtime import PolicyRuntime


def run_development_contract(cases_path: Path, runtime: PolicyRuntime) -> dict[str, Any]:
    rows = [json.loads(line) for line in cases_path.read_text(encoding="utf-8").splitlines() if line]
    passed = 0
    by_passed: Counter[str] = Counter()
    totals: Counter[str] = Counter()
    results = []
    for row in rows:
        _, trace = runtime.evaluate(infer_demo_state(row["input"]))
        fired = {item.policy_id for item in trace if item.fired}
        required = set(row["required_policies"])
        allowed = set(row["allowed_policies"])
        forbidden = set(row["forbidden_policies"])
        ok = required <= fired and not (forbidden & fired) and fired <= required | allowed
        passed += int(ok)
        by_passed[row["category"]] += int(ok)
        totals[row["category"]] += 1
        results.append({
            "id": row["id"], "category": row["category"], "input": row["input"],
            "passed": ok, "required_policies": row["required_policies"],
            "allowed_policies": row["allowed_policies"], "forbidden_policies": row["forbidden_policies"],
            "fired_policies": sorted(fired),
        })
    benign_total = totals["benign"]
    benign_fp = sum(1 for item in results if item["category"] == "benign" and item["fired_policies"])
    return {
        "mode": "offline_demo_fixture",
        "policy_version": runtime.version,
        "passed": passed,
        "total": len(rows),
        "pass_rate": passed / len(rows) if rows else 0,
        "benign_false_positives": benign_fp,
        "benign_total": benign_total,
        "by_category": [{"category": key, "passed": by_passed[key], "total": totals[key]} for key in totals],
        "results": results,
        "claim": "Development contract only. This is not GPT-5.6 performance and supports no generalization claim."
    }
