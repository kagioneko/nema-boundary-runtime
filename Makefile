.PHONY: demo test visual evaluate

demo:
	.venv/bin/python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

test:
	.venv/bin/python -m pytest -q

visual:
	.venv/bin/python tools/visual_check.py

evaluate:
	.venv/bin/python evaluation/run_offline.py
