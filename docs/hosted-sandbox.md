# Hosted Offline Sandbox Plan

## Deployment boundary

- The application listens on `127.0.0.1` only.
- A managed HTTPS reverse proxy or outbound tunnel terminates public TLS.
- No VPS firewall port is opened for the application.
- Public mode remains `offline_demo_fixture`; it needs no OpenAI credential.
- Conversation content is not persisted or logged by the application.

## Quotas

| Route | Default | Notes |
|---|---:|---|
| `POST /api/analyze` | 30/min/client | deterministic fixture |
| `POST /api/replay` | 15/min/client | strict temporary policy bundle |
| health/version/evaluation | unlimited | read-only |

Configure with `NEMA_ANALYZE_PER_MINUTE` and `NEMA_REPLAY_PER_MINUTE` (1..1000). The limiter is process-local and deliberately stores only monotonic timestamps keyed by client IP; it does not store input text. Deploy one worker for predictable demo quota. A production multi-worker deployment would require a shared limiter.

Forwarded headers are ignored by default. `NEMA_TRUSTED_PROXY_IPS` accepts a comma-separated list of literal direct-peer proxy IPs. For the loopback-only cloudflared deployment, set `NEMA_TRUSTED_PROXY_IPS=127.0.0.1,::1`; otherwise all tunnel users share the proxy's quota bucket. Only a single `CF-Connecting-IP` value from a configured direct peer is accepted. `X-Forwarded-For` is always ignored to prevent client-supplied leftmost-address spoofing. Never trust arbitrary public client addresses.

## Public-mode controls

- 64 KiB actual-body limit, independent of `Content-Length`.
- Strict Pydantic schemas and `extra=forbid`.
- Max 64 policies; max 16 conditions/directives per policy.
- No arbitrary operator evaluation, tool execution, persistence, or filesystem writes.
- CSP, frame denial, no-sniff, no-referrer, permissions policy, and no-store API responses.
- Offline and non-generalization disclaimers remain visible.

## Pre-publication checklist

1. Run `make test`, `make visual`, and `make evaluate`.
2. Build and run the non-root Docker image.
3. Confirm public TLS and the exact sandbox hostname.
4. Confirm the app still reports `offline_demo_fixture` at `/ready` and `/version`.
5. Test 429 and `Retry-After` through the real proxy.
6. Verify proxy IP trust configuration; spoofed forwarding headers must not bypass quota.
7. Obtain independent AI security/quality review and record PASS in the private handoff log.
8. Add the sandbox URL to README, Devpost, and the final video.
