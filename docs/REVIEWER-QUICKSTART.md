# Reviewer Quickstart

Use this guide to inspect Agent Meeting Room quickly without reading the whole codebase first.

## What this project demonstrates

- Flask app structure with server-sent event streaming.
- Local model routing through Ollama-compatible models.
- Optional cloud model routing.
- Meeting templates, exports, memory search, and structured deliverables.

## Suggested review path

1. Read `README.md` for feature scope and setup.
2. Inspect `app.py` for routes, streaming, and memory endpoints.
3. Inspect `agents.py` for agent routing and model adapters.
4. Run the test suite before changing behavior.

## Local verification

```bash
python -m pytest
```

If Ollama or cloud API keys are unavailable, focus on tests that mock or bypass external calls. Do not commit secrets or local `.env` files.

