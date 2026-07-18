# Judge test path

1. Start the application using the README.
2. Open `/health` and confirm the policy version.
3. Run the four UI presets and inspect conditions, fired policies, and directives.
4. Run the benign control and confirm that no policy fires.
5. Open `/api/evaluation` or the dashboard to inspect the 40-case development contract.
6. Run `pytest -q`; all tests should pass.

The offline adapter is intentionally deterministic for reproducible judging. It is not GPT-5.6 performance. The final API adapter must preserve the same validated `ControlState` boundary.
