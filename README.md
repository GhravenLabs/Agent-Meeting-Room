<h1 align="center">🏠 Agent Meeting Room</h1>

<p align="center">
  A Flask web app where you <code>@mention</code> AI agents into a live group chat.<br/>
  Local models via Ollama · Claude API on demand · Streaming debates · Obsidian memory
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python" />
  <img src="https://img.shields.io/badge/Flask-2.x-black?style=flat-square&logo=flask" />
  <img src="https://img.shields.io/badge/Ollama-local-orange?style=flat-square" />
  <img src="https://img.shields.io/badge/Claude%20API-optional-purple?style=flat-square" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" />
</p>

<br/>

<p align="center">
  <img src="https://github.com/user-attachments/assets/e5a83e30-a3ad-4379-a6c0-15da952027c2" width="90%" alt="Agent Meeting Room screenshot" />
</p>

---

## What it does

Imagine a group chat where everyone at the table is an AI — each with a different personality, model, and reasoning style. You type a message, mention the agents you want, and they all respond. You can spark a structured debate, run a free-form group discussion via live streaming, or pull in Claude as the senior voice in the room.

- **@mention routing** — only the agents you tag reply
- **Debate mode** — structured 3-round argument with a final summary
- **Free Talk** — agents stream a live discussion on any topic via SSE
- **Memory** — save meeting notes directly to an Obsidian vault
- **@claude** — Claude API joins as the "headmaster" on demand

---

## Agents

All local agents run **any Ollama-compatible model** — swap by editing the `"model"` field in `agents.py`. Defaults are chosen to run under 8GB VRAM.

| Agent | Default Model | VRAM | Personality |
|---|---|---|---|
| `@mistral` | `mistral` | ~4 GB | Sharp analytical thinker |
| `@phi3` | `phi3` | ~2 GB | Creative lateral thinker |
| `@gemma2` | `gemma2:2b` | ~1.5 GB | Balanced careful summarizer |
| `@deepseek` | `deepseek-r1:7b` | ~4.7 GB | Deep step-by-step reasoner |
| `@claude` | `claude-3-5-sonnet-20241022` | API | Collaborative nuanced advisor |

> **Swap a model:** open `agents.py` → change the `"model"` value to anything from `ollama list`.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/Ghraven/agent-meeting-room
cd agent-meeting-room

# 2. Install dependencies
pip install -r requirements.txt

# 3. Pull Ollama models
ollama pull mistral
ollama pull phi3
ollama pull gemma2:2b
ollama pull deepseek-r1:7b

# 4. Set up environment
cp .env.example .env
# Edit .env — add your Anthropic API key (only needed for @claude)

# 5. Run
python app.py
# Windows: double-click start.bat
```

Open **http://localhost:5000**

---

## Usage

| What you type | What happens |
|---|---|
| `@mistral explain quantum computing` | Only Mistral replies |
| `@phi3 @gemma2 brainstorm ideas` | Phi3 and Gemma2 reply |
| `@all what should I build next?` | All local agents reply |
| `@claude review this plan` | Claude API responds |
| `@debate is AI good or bad?` | 3-round structured debate |
| *(no mention)* | All local agents reply |

For **Free Talk**, click the Free Talk button → give a topic → agents discuss live in real time.

---

## Project Structure

```
agent-meeting-room/
├── app.py              Flask routes and SSE streaming
├── agents.py           Agent definitions, Ollama + Claude calls, debate logic
├── memory.py           Obsidian vault integration
├── templates/
│   └── index.html      Single-page frontend (Vanilla JS + SSE)
├── start.bat           Windows one-click launcher
├── .env.example        Environment variable template
└── requirements.txt
```

---

## Requirements

| Requirement | Notes |
|---|---|
| Python 3.11+ | |
| [Ollama](https://ollama.com) | Must be running on port 11434 |
| Anthropic API key | Only needed for `@claude` — optional |
| [Obsidian](https://obsidian.md) | Optional — for memory/note saving |

---

## Tech Stack

**Backend:** Python · Flask · Server-Sent Events  
**Local AI:** Ollama (Mistral · Phi3 · Gemma2 · DeepSeek)  
**Cloud AI:** Anthropic Claude API  
**Frontend:** Vanilla JS · SSE streaming  
**Memory:** Obsidian Markdown vault  

---

## License

MIT — see [LICENSE](LICENSE)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) — adding a new agent takes about 5 lines.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.
