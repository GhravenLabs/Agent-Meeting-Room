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
from urllib import error, request

# Path setup: frozen (exe) vs normal (python launcher.py)
if getattr(sys, 'frozen', False):
    EXE_DIR  = os.path.dirname(sys.executable)
    BASE_DIR = sys._MEIPASS
    os.chdir(EXE_DIR)
else:
    EXE_DIR  = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = EXE_DIR

sys.path.insert(0, BASE_DIR)

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


def main():
    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    from app import app, check_ollama, check_ollama_models, print_startup_banner
    from memory import get_memory_status

    ollama_ok = check_ollama()
    models    = check_ollama_models() if ollama_ok else []
    memory    = get_memory_status()
    print_startup_banner(ollama_ok, models, memory)

    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
