# Changelog

All notable changes to Agent Meeting Room are documented here.

## [Unreleased]

### Added
- Customize room identity, agent names, avatar/logo URLs, accent colors, persona cards, enabled agents, and saved presets from the UI.
- Configure Free Talk duration for 5, 10, 15, or 30 minute sessions.
- Optional browser TTS playback with per-agent voice name hints.

### Planned
- Export meeting transcript as Markdown
- Configurable agent response length via UI slider
- Dark/light theme toggle

---

## [1.7.0] — 2026-05-23

### Added
- **Pluggable memory system** — `MEMORY_BACKEND` env var selects `local` (default), `obsidian`, or `none`
  - `local`: saves notes to `./meeting_notes/` — zero extra software required
  - `obsidian`: original behaviour, requires Obsidian vault path
  - `none`: memory completely disabled
  - `auto`: uses Obsidian if vault path set, otherwise falls back to local
- **Startup check banner** — on launch, app.py now prints Ollama status (running/not + model list), memory backend, and Claude API key status with fix hints
- `/status` endpoint — returns live JSON state of Ollama, memory, and Claude for health checks
- `get_memory_status()` in memory.py — returns active backend info
- `.env.example` fully documented with all variables, options, and examples for Windows/Mac/Linux

### Changed
- Obsidian is now **optional** — local folder memory works out of the box with no extra setup
- Memory save now includes backend name in note metadata

### Fixed
- Startup no longer silently fails when Ollama is offline — clear message with install link printed

---

## [1.6.0] — 2026-05-23

### Added
- `launcher.py` — PyInstaller entry point; starts Flask server and auto-opens browser
- `AgentMeetingRoom.spec` — PyInstaller build spec (single-file portable `.exe`)
- `AgentMeetingRoom_Setup.iss` — Inno Setup installer script (desktop shortcut, Start Menu, Ollama check)
- `build.bat` — one-click Windows build script for the `.exe`
- `.github/workflows/release.yml` — GitHub Actions workflow: push a `v*.*.*` tag → auto-builds and publishes a GitHub Release with `.exe` attached
- `assets/icon.ico`, `assets/icon.png`, `assets/logo.svg` — techy/AI circuit + chat hybrid logo (dark purple/teal)
- README: "Adding your own agents — unlimited LLMs" section with hardware guidance table
- README: Download & install section (portable EXE, full installer, source)

### Changed
- `start.bat` — now checks if Ollama is running before starting Flask, auto-starts it if not

---

## [1.5.0] — 2026-05-23

### Added
- Retry logic in `ask_ollama()` — retries once with a 2s backoff before returning a user-friendly unavailable message (instead of raw exception string)

### Changed
- Updated Claude model to `claude-sonnet-4-5` in `agents.py` and README agents table
- Marked completed milestones: multi-agent chat architecture, Claude headmaster integration, documented + pushed to GitHub

---

## [1.4.0] — 2026-05-21

### Fixed
- Fixed critical bug where the Anthropic API would reject calls due to invalid model name `claude-sonnet-4-6` (updated to `claude-3-5-sonnet-20241022` across `agents.py`, `README.md`, and `CLAUDE.md`)
- Removed `keep_alive: 0` from `ask_ollama` payload to prevent Ollama from constantly unloading models from VRAM between turns, drastically improving multi-agent performance

---

## [1.3.0] — 2026-05-11

### Changed
- Updated Claude model from `claude-sonnet-4-5` to `claude-sonnet-4-6` in `agents.py` and README
- Fixed talk session memory leak — evict oldest session when `talk_sessions` dict exceeds 100 entries
- Fixed missing `anthropic` SDK in `requirements.txt` — was referenced in code but not listed as a dependency
- Improved documentation on model-swap instructions in README agent table

---

## [1.2.0] — 2025-04-30

### Changed
- Restored `deepseek-r1:7b` as the default DeepSeek model (official Ollama tag)
- Added `CONTRIBUTING.md` and `CHANGELOG.md`

---

## [1.1.0] — 2025-04-01

### Added
- `@claude` integration — Claude Sonnet joins as the headmaster agent via Anthropic API
- Free Talk mode — agents hold a live streaming discussion on any topic (SSE)
- Obsidian memory integration — save meeting notes directly to a vault
- Debate mode — 3-round structured argument with Gemma2 summary

### Changed
- Agents now use `keep_alive: 0` to release VRAM after each response

---

## [1.0.0] — 2025-03-01

### Added
- Initial release
- `@mention` routing to local Ollama agents (Mistral, Phi3, Gemma2, DeepSeek)
- Flask backend with SSE streaming
- `@debate` mode with round-by-round structured responses
- `.env.example` for environment configuration
- `start.bat` for one-click Windows launch
