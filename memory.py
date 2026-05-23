"""
memory.py — pluggable memory backend for Agent Meeting Room

Supported backends (set MEMORY_BACKEND in .env):
  obsidian   — saves .md notes to an Obsidian vault folder (default if path set)
  local      — saves to a local folder (no Obsidian needed)
  none       — memory disabled, no files written

To add a custom backend: implement save(title, content) -> bool
and read(max_chars) -> str, then register it in BACKENDS below.
"""
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ── Config ───────────────────────────────────────────────────
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "auto").lower()

# Obsidian vault path — optional
OBSIDIAN_VAULT = os.getenv("OBSIDIAN_VAULT_PATH", "")

# Local fallback folder (used when backend=local or obsidian path not set)
LOCAL_MEMORY_DIR = os.getenv(
    "LOCAL_MEMORY_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "meeting_notes")
)

MEMORY_FILE = "meeting_memory.md"


def _resolve_backend() -> str:
    """Auto-detect which backend to use based on env config."""
    if MEMORY_BACKEND == "none":
        return "none"
    if MEMORY_BACKEND == "obsidian" or (MEMORY_BACKEND == "auto" and OBSIDIAN_VAULT):
        if OBSIDIAN_VAULT:
            return "obsidian"
        print("[Memory] MEMORY_BACKEND=obsidian but OBSIDIAN_VAULT_PATH is not set — falling back to local")
        return "local"
    return "local"


ACTIVE_BACKEND = _resolve_backend()


def _get_memory_dir() -> str:
    """Return the active storage directory."""
    if ACTIVE_BACKEND == "obsidian":
        return OBSIDIAN_VAULT
    return LOCAL_MEMORY_DIR


def save_to_obsidian(title: str, content: str) -> bool:
    """
    Save a note. Works with any backend.
    Name kept as save_to_obsidian for backwards compatibility.
    """
    if ACTIVE_BACKEND == "none":
        return False

    memory_dir = _get_memory_dir()
    try:
        os.makedirs(memory_dir, exist_ok=True)
        timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M")
        safe_title = title.replace(" ", "_").replace("/", "-")[:50]
        filename   = f"{datetime.now().strftime('%Y%m%d_%H%M')}_{safe_title}.md"
        filepath   = os.path.join(memory_dir, filename)

        note_content = f"""# {title}
*Saved: {timestamp}*
*Backend: {ACTIVE_BACKEND}*

{content}

---
#agent-meeting #auto-saved
"""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(note_content)

        # Rolling memory file
        memory_path = os.path.join(memory_dir, MEMORY_FILE)
        with open(memory_path, "a", encoding="utf-8") as f:
            f.write(f"\n## {title} — {timestamp}\n{content}\n\n")

        print(f"[Memory] Saved to {filepath}  (backend: {ACTIVE_BACKEND})")
        return True

    except Exception as e:
        print(f"[Memory] Error saving: {e}")
        return False


def get_recent_memory(max_chars: int = 1500) -> str:
    """Read recent memory context for agents."""
    if ACTIVE_BACKEND == "none":
        return ""

    memory_dir = _get_memory_dir()
    try:
        memory_path = os.path.join(memory_dir, MEMORY_FILE)
        if not os.path.exists(memory_path):
            return ""
        with open(memory_path, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > max_chars:
            content = "..." + content[-max_chars:]
        return content
    except Exception as e:
        print(f"[Memory] Error reading: {e}")
        return ""


def clear_memory() -> bool:
    """Clear the rolling memory file."""
    if ACTIVE_BACKEND == "none":
        return True
    memory_dir = _get_memory_dir()
    try:
        memory_path = os.path.join(memory_dir, MEMORY_FILE)
        if os.path.exists(memory_path):
            os.remove(memory_path)
        return True
    except Exception:
        return False


def get_memory_status() -> dict:
    """Return current memory backend info (used by /status endpoint)."""
    return {
        "backend":    ACTIVE_BACKEND,
        "path":       _get_memory_dir() if ACTIVE_BACKEND != "none" else None,
        "configured": ACTIVE_BACKEND != "none",
    }
