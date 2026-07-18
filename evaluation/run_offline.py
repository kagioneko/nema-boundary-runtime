import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.evaluation import run_development_contract
from app.runtime import PolicyRuntime
result=run_development_contract(ROOT/'evaluation/cases.jsonl', PolicyRuntime(ROOT/'policies/default.json'))
print(json.dumps(result,ensure_ascii=False,indent=2))
