import json
import sys
from pathlib import Path
import httpx
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'backend'))
from app.openrouter_adapter import OpenRouterAdapter, PROVIDER_LOCK

VALID_STATE={"arousal":.2,"distress":.3,"decision_dependency":.4,"emotional_intensity":.5,"uncertainty":.6,"urgency":.1,"exclusive_attachment":.2,"support_escalation":"none"}

def test_structured_request_locks_model_provider_and_schema():
    seen={}
    def handler(request):
        seen['auth']=request.headers['authorization']; seen['body']=json.loads(request.content)
        return httpx.Response(200,json={"id":"x","model":"openai/gpt-5.6-sol","provider":"openai","choices":[{"message":{"content":json.dumps(VALID_STATE)}}],"usage":{"prompt_tokens":1,"completion_tokens":1}})
    adapter=OpenRouterAdapter('test-secret',transport=httpx.MockTransport(handler))
    state,meta=adapter.infer_state('test')
    assert state.distress==.3 and meta['model']=='openai/gpt-5.6-sol'
    assert seen['auth']=='Bearer test-secret'
    assert seen['body']['provider']==PROVIDER_LOCK
    assert seen['body']['response_format']['json_schema']['strict'] is True
    assert seen['body']['response_format']['json_schema']['schema']['additionalProperties'] is False

def test_rejects_non_gpt_56_model():
    with pytest.raises(ValueError): OpenRouterAdapter('x',model='openai/gpt-5.5')

def test_rejects_unexpected_returned_model():
    def handler(request):
        return httpx.Response(200,json={"model":"other/model","choices":[{"message":{"content":"{}"}}]})
    with pytest.raises(RuntimeError): OpenRouterAdapter('x',transport=httpx.MockTransport(handler)).infer_state('x')
