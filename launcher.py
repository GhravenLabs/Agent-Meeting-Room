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

PORT = int(os.getenv('PORT', 5000))
URL  = f'http://localhost:{PORT}'


def open_browser():
    time.sleep(2.0)
    webbrowser.open(URL)


def main():
    threading.Thread(target=open_browser, daemon=True).start()

    from app import app, check_ollama, check_ollama_models, print_startup_banner
    from memory import get_memory_status

    ollama_ok = check_ollama()
    models    = check_ollama_models() if ollama_ok else []
    memory    = get_memory_status()
    print_startup_banner(ollama_ok, models, memory)

    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
