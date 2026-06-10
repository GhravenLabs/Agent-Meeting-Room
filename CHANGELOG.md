# Changelog

All notable changes to Agent Meeting Room are documented here.

## [Unreleased]

### Added
- Project Context import for loading local repo/folder summaries into future agent prompts.
- `docs/ROADMAP.md` for tracking the next product improvements day by day.
- Configurable agent response length via a room settings slider.
- Dark/light theme toggle with persisted room preference.

---

## [1.10.0] - 2026-06-09

### Added
- Optional Pake desktop shell build path for wrapping the local Flask UI in a native desktop window.
- Tauri desktop shell build that bundles and launches the Flask backend sidecar automatically.
- Structured Delivery generator for turning the current meeting into Markdown PR descriptions, issue drafts, implementation plans, research briefs, release notes, bug reports, and review summaries.
- Meeting History panel with searchable current-room messages, participant stats, jump-to-message links, and backend history restore on reload.
- Optional TurboVec semantic memory scaffold with Ollama embeddings, semantic note indexing, and Keyword/Semantic modes in memory search.

---

## [1.9.0] - 2026-06-08

### Added
- Meeting templates for Code Review, Product Debate, Research, and Planning rooms with starter prompts.
- Search saved local/Obsidian Markdown memory notes from the room UI.
- Export the current meeting transcript as a Markdown download from the room header.
- Optional Codex/OpenAI and Gemini/Google cloud agents with `@codex`, `@gemini`, and `@google` mention routing.

### Fixed
- Packaged launcher now validates `PORT`, waits for Flask to respond, and only then opens the browser.
- Claude API responses now check HTTP status before parsing JSON, making API failures easier to diagnose.

---

## [1.8.0] - 2026-06-03

### Added
- Customize room identity, agent names, avatar/logo URLs, accent colors, persona cards, enabled agents, and saved presets from the UI.
- Configure Free Talk duration for 5, 10, 15, or 30 minute sessions.
- Optional browser TTS playback with per-agent voice name hints.
- `.env.example`, `test.bat`, and contributor testing notes for easier local setup.
- Focused tests for customization persistence, Flask route validation, memory filename handling, and core app routes.

### Changed
- Honored the configured `PORT` environment variable when starting the app.
- Shared Free Talk duration clamping across routes and tests.
- Updated repository links to the `GhravenLabs` organization.

### Fixed
- Rejected malformed or missing JSON request bodies instead of raising route errors.
- Made the startup banner encoding safer on Windows terminals.
- Normalized customization presets before saving/loading them.
- Prevented empty memory notes and sanitized memory note filenames.
- Ignored malformed Ollama model entries during startup/status checks.
- Validated configured port ranges.
- Capped conversation history after bulk replies.
- Pruned Free Talk sessions before session storage overflow.

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
- Claude agent command integration — Claude Sonnet joins as the headmaster agent via Anthropic API
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
