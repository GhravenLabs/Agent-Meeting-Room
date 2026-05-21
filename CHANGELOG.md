# Changelog

All notable changes to Agent Meeting Room are documented here.

## [Unreleased]

### Planned
- Export meeting transcript as Markdown
- Configurable agent response length via UI slider
- Dark/light theme toggle

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
