"""
Agent Meeting Room — launcher.py
Bundled entry point used by PyInstaller.
Starts the Flask server then opens the browser automatically.
"""
import sys
import os
import threading
import webbrowser
import time

# When frozen by PyInstaller, _MEIPASS holds the temp extraction dir
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
    # Also set working dir so .env and templates are found
    os.chdir(os.path.dirname(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add base dir to path so app/agents/memory imports resolve
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(sys.executable) if getattr(sys,'frozen',False) else BASE_DIR, '.env'))

PORT = int(os.getenv('PORT', 5000))
URL  = f'http://localhost:{PORT}'


def open_browser():
    """Wait a moment for Flask to start, then open the default browser."""
    time.sleep(1.8)
    webbrowser.open(URL)


def main():
    # Open browser in background thread
    t = threading.Thread(target=open_browser, daemon=True)
    t.start()

    # Start Flask (import here so PyInstaller can find it)
    from app import app
    print(f'[AMR] Starting Agent Meeting Room on {URL}')
    print(f'[AMR] Ollama must be running on localhost:11434')
    print(f'[AMR] Press Ctrl+C to stop')
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)


if __name__ == '__main__':
    main()
