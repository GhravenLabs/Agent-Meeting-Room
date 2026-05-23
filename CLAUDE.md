# Agent Meeting Room — Project Context

## What this project is
A Flask multi-agent AI chat app running at localhost:5000. Users @mention agents to summon them into a conversation. Agents are powered by local Ollama models or the Claude API.

## Stack
- Python 3.11, Flask
- Local agents via Ollama: Mistral, Phi3, Gemma2:2b, DeepSeek-r1:7b (unlimited — add any Ollama model in agents.py AGENTS dict)
- Cloud agent: Anthropic Claude API (`claude-sonnet-4-5`)
- Frontend: Vanilla JS with Server-Sent Events for streaming
- Memory: Obsidian Markdown vault

## Key files
- `app.py` — Flask routes, SSE streaming (`/talk_stream/<id>`), session management
- `agents.py` — Agent definitions, `ask_ollama()`, `ask_claude()`, `run_debate()`, `run_free_talk_thread()`
- `memory.py` — Obsidian vault read/write, rolling memory file
- `templates/index.html` — Complete single-page UI

## Modes
- **Structured chat** — `@mention` one or more agents, they each respond once
- **Debate mode** — `@debate <question>` — 3 rounds: independent answers → reactions → Gemma2 summary
- **Free Talk** — `/talk` endpoint + `/talk_stream/<id>` SSE — agents discuss a topic in a loop for up to 5 minutes

## Agent routing logic (agents.py `run_agents`)
1. `@debate` → `run_debate()`
2. `@claude` → `ask_claude()` only
3. `@<name>` → specific agent(s)
4. `@all` or no mention → all 4 local agents

## Environment variables
- `ANTHROPIC_API_KEY` — required for Claude
- `OBSIDIAN_VAULT_PATH` — optional, defaults to `C:/Users/Administrator/Documents/ObsidianVault/AgentMeetings`

## Dev notes
- Ollama must be running on `localhost:11434` before starting the app
- `keep_alive: 0` is set in Ollama calls to unload models from VRAM after each response (RAM-friendly)
- Conversation history is capped at 50 messages in-memory (no DB)
- Free Talk sessions use `threading.Event` for graceful stop

## Release / distribution
- `launcher.py` — PyInstaller entry point (auto-opens browser, loads .env from exe dir)
- `AgentMeetingRoom.spec` — PyInstaller single-file build spec
- `AgentMeetingRoom_Setup.iss` — Inno Setup v6 installer script
- `build.bat` — one-click build on Windows
- `.github/workflows/release.yml` — push tag `v*.*.*` to trigger automated build + GitHub Release
- `assets/icon.ico` — app icon for exe and installer

