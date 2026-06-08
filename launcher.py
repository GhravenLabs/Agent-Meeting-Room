"""
Agent Meeting Room - launcher.py
PyInstaller entry point.
Starts Flask server and opens browser automatically.
"""
import sys
import os
import threading
import webbrowser
import time
import ctypes
from urllib import error, request

DESKTOP_DATA_DIR = os.getenv("AGENT_MEETING_ROOM_DATA_DIR")

# Path setup: frozen (exe) vs normal (python launcher.py)
if getattr(sys, 'frozen', False):
    EXE_DIR  = DESKTOP_DATA_DIR or os.path.dirname(sys.executable)
    BASE_DIR = sys._MEIPASS
else:
    EXE_DIR  = DESKTOP_DATA_DIR or os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = EXE_DIR

os.makedirs(EXE_DIR, exist_ok=True)
os.chdir(EXE_DIR)
sys.path.insert(0, BASE_DIR)

if DESKTOP_DATA_DIR:
    os.environ.setdefault("LOCAL_MEMORY_PATH", os.path.join(EXE_DIR, "meeting_notes"))
    os.environ.setdefault("AGENT_PROFILES_PATH", os.path.join(EXE_DIR, "agent_profiles.json"))

from dotenv import load_dotenv
load_dotenv(os.path.join(EXE_DIR, '.env'), override=False)

DEFAULT_PORT = 5000


def get_launcher_port() -> int:
    """Return a valid local port for the packaged launcher."""
    try:
        port = int(os.getenv("PORT", DEFAULT_PORT))
    except ValueError:
        return DEFAULT_PORT
    if 1 <= port <= 65535:
        return port
    return DEFAULT_PORT


PORT = get_launcher_port()
URL = f"http://127.0.0.1:{PORT}"


def wait_for_server(url: str, timeout: float = 12.0, interval: float = 0.25) -> bool:
    """Wait until Flask is reachable before opening the browser window."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with request.urlopen(url, timeout=1):
                return True
        except (OSError, error.URLError):
            time.sleep(interval)
    return False


def open_browser_when_ready(url: str = URL) -> bool:
    if not wait_for_server(url):
        print(f"Agent Meeting Room did not become ready at {url}")
        return False
    webbrowser.open(url)
    return True


def process_exists(pid: int) -> bool:
    """Return whether a process id still exists."""
    if pid <= 0:
        return False
    if os.name == "nt":
        process_query_limited_information = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            process_query_limited_information,
            False,
            pid,
        )
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def exit_when_parent_exits(interval: float = 2.0):
    """Exit the backend if it was launched by a desktop shell that is gone."""
    try:
        parent_pid = int(os.getenv("AGENT_MEETING_ROOM_PARENT_PID", "0"))
    except ValueError:
        return
    if parent_pid <= 0:
        return

    def monitor_parent():
        while True:
            if not process_exists(parent_pid):
                os._exit(0)
            time.sleep(interval)

    threading.Thread(target=monitor_parent, daemon=True).start()


def main():
    if os.getenv("AGENT_MEETING_ROOM_DESKTOP") != "1":
        threading.Thread(target=open_browser_when_ready, daemon=True).start()
    else:
        exit_when_parent_exits()

    from app import app, check_ollama, check_ollama_models, print_startup_banner
    from memory import get_memory_status

    ollama_ok = check_ollama()
    models    = check_ollama_models() if ollama_ok else []
    memory    = get_memory_status()
    print_startup_banner(ollama_ok, models, memory)

    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
