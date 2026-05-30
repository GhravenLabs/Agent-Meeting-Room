# Contributing to Agent Meeting Room

Thanks for your interest in contributing! This is a small project built for learning and fun — all contributions welcome.

## Ways to contribute

- **Bug reports** — open an issue describing what happened, what you expected, and your Python / Ollama versions
- **New agents** — add an entry to the `AGENTS` dict in `agents.py` with a model, color, and personality
- **UI improvements** — the frontend lives in `templates/index.html` — Vanilla JS + SSE
- **Feature ideas** — open an issue to discuss before building

## Local setup

```bash
git clone https://github.com/GhravenLabs/Agent-Meeting-Room
cd Agent-Meeting-Room
pip install -r requirements.txt
cp .env.example .env   # add your Anthropic key if testing @claude
ollama pull mistral    # pull at least one model
python app.py
```

## Adding a new agent

Open `agents.py` and add an entry to the `AGENTS` dict:

```python
"mynewagent": {
    "model":       "any-ollama-model",
    "name":        "MyNewAgent",
    "color":       "#HEXCOLOR",
    "personality": "You are ... Keep responses under 150 words."
}
```

Then mention it in chat as `@mynewagent`. That's it.

## Code style

- Python 3.11+, no external frameworks beyond Flask + requests
- Keep `agents.py` logic-only (no Flask routes)
- Keep `app.py` routes-only (no agent logic)
- Use `python -m unittest discover -s tests` before opening a PR
- On Windows, `test.bat` runs the same test suite

## Pull requests

1. Fork the repo and create a branch from `main`
2. Make your change
3. Test it works locally
4. Open a PR with a short description of what you changed and why

No CLA, no formal review process — just a quick check that it works.
