from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import FastAPI, Request
from pydantic import ConfigDict
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .generation import baseline_demo, controlled_demo
from .evaluation import run_development_contract
from .inference import infer_demo_state
from .models import AnalysisResult, AnalyzeRequest
from .runtime import PolicyBundle, PolicyRuntime
from .verifier import verify_response


class ReplayRequest(AnalyzeRequest):
    model_config = ConfigDict(extra="forbid")
    policy_bundle: PolicyBundle

PROJECT = Path(__file__).resolve().parents[2]
PROFILE = json.loads((PROJECT / "profiles/gpt-5.6-sol.json").read_text())
RUNTIME = PolicyRuntime(PROJECT / "policies/default.json")

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'",
    "Cache-Control": "no-store",
}


class RateLimitMiddleware:
    """Process-local demo quota. No request content or persistent logs are stored."""
    def __init__(self, app, limits: dict[tuple[str, str], int] | None = None, window_seconds: int = 60, trusted_proxies: set[str] | None = None, max_buckets: int = 10000):
        self.app = app
        self.limits = limits or {("POST", "/api/analyze"): 30, ("POST", "/api/replay"): 15}
        self.window_seconds = window_seconds
        self.trusted_proxies = trusted_proxies or set()
        self.max_buckets = max_buckets
        self.buckets: dict[tuple[str, str, str], deque[float]] = defaultdict(deque)

    def _client_ip(self, scope) -> str:
        peer = (scope.get("client") or ("unknown", 0))[0]
        candidate = peer
        if peer in self.trusted_proxies:
            connecting = [
                value.decode("latin1").strip()
                for name, value in scope.get("headers", [])
                if name.decode("latin1").lower() == "cf-connecting-ip"
            ]
            if len(connecting) == 1:
                candidate = connecting[0]
        try:
            return str(ipaddress.ip_address(candidate))
        except ValueError:
            return "unknown"

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        route = (scope.get("method", "GET"), scope.get("path", ""))
        limit = self.limits.get(route)
        if limit is None:
            return await self.app(scope, receive, send)
        now = time.monotonic()
        key = (self._client_ip(scope), *route)
        if key not in self.buckets and len(self.buckets) >= self.max_buckets:
            self.buckets.pop(next(iter(self.buckets)))
        bucket = self.buckets[key]
        cutoff = now - self.window_seconds
        while bucket and bucket[0] <= cutoff:
            bucket.popleft()
        if len(bucket) >= limit:
            retry_after = max(1, int(self.window_seconds - (now - bucket[0])) + 1)
            response = JSONResponse({"detail": "demo quota exceeded"}, status_code=429, headers={**SECURITY_HEADERS,
                "Retry-After": str(retry_after), "X-RateLimit-Limit": str(limit), "X-RateLimit-Remaining": "0",
            })
            return await response(scope, receive, send)
        bucket.append(now)
        remaining = max(0, limit - len(bucket))
        async def send_with_headers(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.extend([(b"x-ratelimit-limit", str(limit).encode()), (b"x-ratelimit-remaining", str(remaining).encode()), (b"cache-control", b"no-store")])
                message["headers"] = headers
            await send(message)
        return await self.app(scope, receive, send_with_headers)


def _positive_limit(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc
    if not 1 <= value <= 1000:
        raise RuntimeError(f"{name} must be between 1 and 1000")
    return value


def _demo_limits() -> dict[tuple[str, str], int]:
    return {
        ("POST", "/api/analyze"): _positive_limit("NEMA_ANALYZE_PER_MINUTE", 30),
        ("POST", "/api/replay"): _positive_limit("NEMA_REPLAY_PER_MINUTE", 15),
    }

def _trusted_proxy_ips() -> set[str]:
    raw = os.getenv("NEMA_TRUSTED_PROXY_IPS", "")
    result = set()
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            result.add(str(ipaddress.ip_address(item)))
        except ValueError:
            raise RuntimeError("NEMA_TRUSTED_PROXY_IPS must contain literal IP addresses")
    return result

class BodyLimitMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            if message["type"] == "http.request":
                body.extend(message.get("body", b""))
                if len(body) > self.max_bytes:
                    response = JSONResponse({"detail": "request body too large"}, status_code=413, headers=SECURITY_HEADERS)
                    return await response(scope, receive, send)
                if not message.get("more_body", False):
                    break
        delivered = False
        async def replay_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}
        return await self.app(scope, replay_receive, send)

app = FastAPI(title="NEMA Boundary Runtime", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["GET", "POST"], allow_headers=["content-type"])
app.add_middleware(BodyLimitMiddleware, max_bytes=64 * 1024)
app.add_middleware(RateLimitMiddleware, limits=_demo_limits(), trusted_proxies=_trusted_proxy_ips())

MAX_BODY_BYTES = 64 * 1024

def _secure(response):
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    return response

@app.middleware("http")
async def request_limits_and_headers(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > MAX_BODY_BYTES:
                return _secure(JSONResponse({"detail": "request body too large"}, status_code=413))
        except ValueError:
            return _secure(JSONResponse({"detail": "invalid content-length"}, status_code=400))
    return _secure(await call_next(request))

@app.get("/")
def index() -> FileResponse:
    return FileResponse(PROJECT / "frontend/index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "policy_version": RUNTIME.version}

@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready", "inference_mode": "offline_demo_fixture"}

@app.get("/version")
def version() -> dict[str, str]:
    policy_path = PROJECT / "policies/default.json"
    profile_path = PROJECT / "profiles/gpt-5.6-sol.json"
    return {
        "app_version": app.version,
        "policy_version": RUNTIME.version,
        "policy_sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest(),
        "profile_sha256": hashlib.sha256(profile_path.read_bytes()).hexdigest(),
        "inference_mode": "offline_demo_fixture",
    }


def _analyze(request: AnalyzeRequest, runtime: PolicyRuntime) -> AnalysisResult:
    inference_text = "\n".join([*request.history, request.text])
    state = request.state_override or infer_demo_state(inference_text)
    mode = "state_override" if request.state_override else "offline_demo"
    directives, trace = runtime.evaluate(state)
    fired = [item.policy_id for item in trace if item.fired]
    reasons = [
        f"{item.policy_id} fired at priority {item.priority}: " +
        ", ".join(f"{c.field} {c.op} {c.expected} (observed {c.observed})" for c in item.conditions)
        for item in trace if item.fired
    ]
    baseline_response = baseline_demo(request.text)
    controlled_response = controlled_demo(request.text, directives)
    return AnalysisResult(
        profile_id=PROFILE["profile_id"], policy_version=runtime.version,
        inference_mode=mode, state=state, fired_policies=fired, directives=directives,
        trace=trace, baseline_response=baseline_response,
        controlled_response=controlled_response, change_reasons=reasons,
        verification=verify_response(controlled_response, directives),
    )

@app.post("/api/analyze", response_model=AnalysisResult)
def analyze(request: AnalyzeRequest) -> AnalysisResult:
    return _analyze(request, RUNTIME)

@app.get("/api/policies")
def policies():
    return RUNTIME.bundle.model_dump(mode="json")

@app.post("/api/replay", response_model=AnalysisResult)
def replay(request: ReplayRequest) -> AnalysisResult:
    base = AnalyzeRequest(text=request.text, history=request.history, state_override=request.state_override)
    return _analyze(base, PolicyRuntime.from_bundle(request.policy_bundle))


@app.get("/api/evaluation")
def evaluation_summary():
    return run_development_contract(PROJECT / "evaluation/cases.jsonl", RUNTIME)
