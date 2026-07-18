# NEMA Boundary Runtime

Turn conversational signals into executable AI safety policies.

NEMA Boundary Runtime is an inspectable Developer Tool that converts inferred conversational control signals into deterministic response directives. The MVP makes the full path visible: **signals → fired policies → controlled response**.

> This is a behavioral control prototype, not a medical or psychological diagnostic system. It does not measure neurotransmitters or guarantee prevention of dependency or harm.

## What is implemented

- validated `ControlState` schema;
- priority-ordered deterministic policy runtime;
- condition-level execution trace;
- autonomy, urgency, distress, exclusive-attachment, and support-escalation policies;
- baseline/controlled response comparison;
- responsive browser demo;
- offline deterministic fixture for repeatable judging and tests.
- 40-case stratified development contract and dashboard.

The offline fixture is deliberately labeled and is **not** presented as a trained classifier. A GPT-5.6 structured-output adapter is the next integration step.

## Live hosted sandbox

Try the reviewed offline demo at **https://nema.kagioneko.com/**. It uses deterministic fixtures, requires no API credential, stores no conversation text, and applies per-client demo quotas.

[Watch the captioned 2m11s demo](https://www.youtube.com/watch?v=PE7fCeTxB38)

![NEMA Boundary Runtime desktop interface](artifacts/desktop.png)

## Run locally

Supported: Linux/macOS/Windows with Python 3.11+.

### Docker

```bash
docker build -t nema-boundary-runtime .
docker run --rm -p 127.0.0.1:8000:8000 nema-boundary-runtime
```

### Python

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
uvicorn app.main:app --app-dir backend --reload
```

Open <http://127.0.0.1:8000>.

## Test

```bash
pytest
```

## Architecture

```text
input -> structured signal adapter -> ControlState validation
      -> deterministic policy runtime -> directives + trace
      -> response adapter -> baseline/controlled comparison
```

Policy data lives in `policies/default.json`; the model profile is in `profiles/gpt-5.6-sol.json`. See `docs/specification.md` for the frozen MVP boundary and evaluation plan. Demo and judging paths are in `docs/demo-script.md` and `docs/judge-test.md`.

## Credential handling

No credential is required for offline demo mode. Production API credentials must be retrieved at runtime from Vault; do not place them in code, `.env`, logs, crontab, or repository history.

## Build Week notes

The project targets **Developer Tools**. Before submission, add the 40-case evaluation artifact, Codex `/feedback` session ID, public demo video, and a description of where Codex accelerated implementation. External publication is blocked until the required independent AI security/quality review is recorded in the private operator handoff log.

### Windows activation

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```bat
.venv\Scripts\activate.bat
```

## Browser visual check

```bash
pip install -r requirements-dev.txt
playwright install chromium
python tools/visual_check.py
```

The check starts a loopback-only temporary server, exercises policy replay and primary flows at desktop/mobile sizes, verifies diff, execution trace, the 40-case dashboard/details, fails on browser errors, and writes screenshots to `artifacts/`.

## Hosted demo safety

The public sandbox must remain offline-only until the final GPT-5.6 adapter is explicitly enabled. Default process-local quotas are 30 analyze requests and 15 replay requests per client per minute:

```bash
NEMA_ANALYZE_PER_MINUTE=30
NEMA_REPLAY_PER_MINUTE=15
# Trust forwarding headers only from literal direct-peer proxy IPs:
NEMA_TRUSTED_PROXY_IPS=
```

The application stores no conversation text in its limiter. See `docs/hosted-sandbox.md` for the deployment boundary and proxy checklist.
