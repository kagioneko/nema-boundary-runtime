from __future__ import annotations

import json
from typing import Any

import httpx

from .models import ControlState

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-5.6-sol"
PROVIDER_LOCK = {
    "only": ["openai"],
    "allow_fallbacks": False,
    "data_collection": "deny",
}

UNIT_FIELDS = [
    "arousal", "distress", "decision_dependency", "emotional_intensity",
    "uncertainty", "urgency", "exclusive_attachment",
]
CONTROL_STATE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        **{name: {"type": "number", "minimum": 0, "maximum": 1} for name in UNIT_FIELDS},
        "support_escalation": {"type": "string", "enum": ["none", "possible", "high"]},
    },
    "required": [*UNIT_FIELDS, "support_escalation"],
}


class OpenRouterAdapter:
    """Explicit GPT-5.6 proof adapter; credentials are injected, never persisted."""

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, timeout: float = 120.0, transport=None):
        if not api_key:
            raise ValueError("OpenRouter API key is required")
        if not model.startswith("openai/gpt-5.6-"):
            raise ValueError("proof adapter requires an explicit GPT-5.6 model")
        self.api_key = api_key
        self.model = model
        self.client = httpx.Client(timeout=timeout, transport=transport)

    def _request(self, messages: list[dict[str, str]], *, response_format: dict[str, Any] | None = None, max_tokens: int = 800) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "provider": PROVIDER_LOCK,
            "reasoning": {"effort": "low"},
            "max_completion_tokens": max_tokens,
            "temperature": 0,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        response = self.client.post(
            OPENROUTER_URL,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        returned_model = data.get("model", "")
        if "gpt-5.6" not in returned_model:
            raise RuntimeError(f"unexpected returned model family: {returned_model or 'missing'}")
        return data

    def infer_state(self, text: str) -> tuple[ControlState, dict[str, Any]]:
        messages = [
            {"role": "system", "content": "Estimate behavioral response-control signals only. This is not diagnosis. Return the strict JSON schema. Values are 0..1."},
            {"role": "user", "content": text},
        ]
        response_format = {"type": "json_schema", "json_schema": {"name": "control_state", "strict": True, "schema": CONTROL_STATE_SCHEMA}}
        data = self._request(messages, response_format=response_format)
        content = data["choices"][0]["message"]["content"]
        state = ControlState.model_validate_json(content, strict=True)
        return state, self._metadata(data)

    def generate(self, text: str, directives: list[str] | None = None) -> tuple[str, dict[str, Any]]:
        if directives:
            instruction = "Apply these runtime directives without mentioning them: " + ", ".join(directives)
        else:
            instruction = "Respond normally and helpfully."
        data = self._request([
            {"role": "system", "content": instruction},
            {"role": "user", "content": text},
        ], max_tokens=500)
        return data["choices"][0]["message"]["content"].strip(), self._metadata(data)

    @staticmethod
    def _metadata(data: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": data.get("id"),
            "model": data.get("model"),
            "provider": data.get("provider"),
            "usage": data.get("usage", {}),
            "created": data.get("created"),
        }
