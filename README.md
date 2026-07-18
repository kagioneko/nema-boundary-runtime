# NEMA Boundary Runtime

[Live Sandbox](https://nema.kagioneko.com/) · [Demo Video](https://www.youtube.com/watch?v=PE7fCeTxB38) · [Source](https://github.com/kagioneko/nema-boundary-runtime)

Turn conversational signals into executable AI safety policies.

NEMA stands for **Neurostate Machine Language**. NEMA Boundary Runtime is an inspectable Developer Tool that converts inferred conversational control signals into deterministic response directives. The MVP makes the full path visible: **signals → fired policies → controlled response**.

> This is a behavioral control prototype, not a medical or psychological diagnostic system. It does not measure neurotransmitters or guarantee prevention of dependency or harm.

## What is implemented

- validated `ControlState` schema;
- priority-ordered deterministic policy runtime;
- condition-level execution trace;
- autonomy, urgency, distress, exclusive-attachment, and support-escalation policies;
- baseline/controlled response comparison;
- responsive browser demo;
- offline deterministic fixture for repeatable judging and tests;
- 40-case stratified development contract and dashboard;
- a four-scenario, 12-call GPT-5.6 Sol API proof through OpenRouter;
- a limited post-generation directive verifier with `PASS` / `VIOLATION` / `REVIEW` results.

The offline fixture is deliberately labeled and is **not** presented as a trained classifier. A separate limited API proof uses GPT-5.6 Sol Structured Outputs for state inference and GPT-5.6 Sol for baseline/controlled generation. It is evidence of integration, not a benchmark or generalization result.

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

## Limited GPT-5.6 API proof

The reproducible proof script retrieves the OpenRouter key from Vault at runtime, pins `openai/gpt-5.6-sol`, restricts routing to the OpenAI provider, disables fallbacks, and requests denial of provider data collection:

```bash
python tools/run_openrouter_proof.py --dry-run
python tools/run_openrouter_proof.py
```

The reviewed four-scenario artifact is in `evaluation/results/openrouter-gpt-5.6-proof.json`: 12 successful calls, returned model `openai/gpt-5.6-sol`, provider `OpenAI`, 3,505 total tokens, and reported cost **$0.08235**. This small proof is intentionally separate from the deterministic 40-case development contract.

## Verification boundary

NEMA now performs deterministic post-generation checks for a narrow set of observable requirements, including decision takeover, autonomy return, exclusive relational claims, human-support language, and pause/confirmation language. Directives that cannot be reliably verified with phrase rules are marked `REVIEW`, not silently passed. This closes part of the enforcement gap but does not guarantee semantic compliance. Directive priority currently controls deterministic ordering and deduplication; semantic conflict arbitration is explicitly future work. MVP thresholds are hypothesis-driven defaults, not statistically calibrated cutoffs.

## Credential handling

No credential is required for offline demo mode. Production API credentials must be retrieved at runtime from Vault; do not place them in code, `.env`, logs, crontab, or repository history.

## How Codex contributed

Codex was the primary implementation partner during OpenAI Build Week. It translated the initial product specification into the FastAPI/Pydantic runtime, policy schema, execution trace, Policy Lab replay UI, deterministic and adversarial tests, Playwright desktop/mobile harness, non-root Docker packaging, hosted-sandbox quota controls, OpenRouter GPT-5.6 proof adapter, and the limited post-generation verifier. Codex also ran regression checks and prepared publication candidates for independent review.

Human decisions defined the product boundary and research claims: treating NeuroState/ControlState as a behavioral control representation rather than biology or diagnosis; keeping policy firing deterministic; separating the 40-case conformance contract from model-performance evidence; requiring Vault-backed credentials; limiting the API proof to four synthetic scenarios; and refusing to claim semantic guarantees, threshold calibration, or universal effectiveness. Independent AI reviews were used as publication gates, and their blocking findings were fixed before release.

## Build Week notes

The project targets **Developer Tools**. The Codex `/feedback` requirement is complete; the remaining gates are final public YouTube visibility and final Devpost form review. Independent review for the current release is complete; any future public change must receive a new security/quality review recorded in the private operator handoff log.

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
