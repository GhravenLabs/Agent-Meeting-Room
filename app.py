from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from agents import run_agents, run_free_talk_thread
from memory import save_to_obsidian, get_recent_memory, get_memory_status
from customization import load_config, save_config, get_room_config
import os
import sys
import json
import queue
import threading
import uuid
import requests as http_requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
conversation_history = []
talk_sessions    = {}   # session_id -> queue.Queue
talk_stop_events = {}   # session_id -> threading.Event


# ── Startup checks ────────────────────────────────────────────
def check_ollama() -> bool:
    """Return True if Ollama is reachable on localhost:11434."""
    try:
        r = http_requests.get("http://localhost:11434", timeout=3)
        return r.status_code < 500
    except Exception:
        return False


def check_ollama_models() -> list:
    """Return list of pulled Ollama model names."""
    try:
        r = http_requests.get("http://localhost:11434/api/tags", timeout=5)
        if r.status_code == 200:
            return [m["name"] for m in r.json().get("models", [])]
    except Exception:
        pass
    return []


def _safe_print(message=""):
    """Print startup text even when Windows stdout uses a narrow encoding."""
    try:
        print(message)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(str(message).encode(encoding, errors="replace").decode(encoding))


def print_startup_banner(ollama_ok: bool, models: list, memory: dict):
    sep = "=" * 50
    _safe_print(sep)
    _safe_print("  Agent Meeting Room")
    _safe_print(sep)

    # Ollama
    if ollama_ok:
        _safe_print(f"  ✓ Ollama running  ({len(models)} model(s) available)")
        if models:
            for m in models[:6]:
                _safe_print(f"      · {m}")
            if len(models) > 6:
                _safe_print(f"      ... and {len(models)-6} more")
    else:
        _safe_print("  ✗ Ollama NOT found — local agents will not respond")
        _safe_print("    → Install: https://ollama.com")
        _safe_print("    → Then run: ollama pull mistral")

    # Memory
    mem_backend = memory["backend"]
    if mem_backend == "obsidian":
        _safe_print(f"  ✓ Memory: Obsidian vault  ({memory['path']})")
    elif mem_backend == "local":
        _safe_print(f"  ✓ Memory: local folder  ({memory['path']})")
    else:
        _safe_print("  · Memory: disabled  (set MEMORY_BACKEND=local to enable)")

    # Claude
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key and not api_key.startswith("your_"):
        _safe_print("  ✓ Claude API key found  (@claude available)")
    else:
        _safe_print("  · Claude API: no key set  (@claude will not respond)")
        _safe_print("    → Add ANTHROPIC_API_KEY to .env for @claude")

    _safe_print(sep)
    _safe_print("  Open: http://localhost:5000")
    _safe_print(sep)


# ── Routes ───────────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/status")
def status():
    """Health/status endpoint — used by frontend to show live state."""
    ollama_ok = check_ollama()
    models    = check_ollama_models() if ollama_ok else []
    memory    = get_memory_status()
    api_key   = os.getenv("ANTHROPIC_API_KEY", "")
    return jsonify({
        "ollama":  {"running": ollama_ok, "models": models},
        "memory":  memory,
        "claude":  {"configured": bool(api_key and not api_key.startswith("your_"))},
        "customization": load_config(),
    })


@app.route("/customization", methods=["GET"])
def get_customization():
    return jsonify(load_config())


@app.route("/customization", methods=["POST"])
def update_customization():
    data = request.get_json(silent=True) or {}
    return jsonify(save_config(data))


@app.route("/customization/reset", methods=["POST"])
def reset_customization():
    from customization import default_config

    return jsonify(save_config(default_config()))


@app.route("/chat", methods=["POST"])
def chat():
    data     = request.get_json(silent=True) or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "empty message"}), 400

    conversation_history.append({"role": "user", "content": user_msg})
    memory_context = get_recent_memory()
    responses = run_agents(user_msg, conversation_history, memory_context)

    for r in responses:
        conversation_history.append({"role": r["agent"], "content": r["message"]})
    if len(conversation_history) > 50:
        conversation_history.pop(0)

    return jsonify({"responses": responses})


@app.route("/save_memory", methods=["POST"])
def save_memory():
    data    = request.get_json(silent=True) or {}
    content = data.get("content", "").strip()
    title   = data.get("title", "Meeting note").strip() or "Meeting note"
    if not content:
        return jsonify({"error": "empty content"}), 400
    result  = save_to_obsidian(title, content)
    return jsonify({"saved": result, "backend": get_memory_status()["backend"]})


@app.route("/clear", methods=["POST"])
def clear():
    conversation_history.clear()
    return jsonify({"cleared": True})


@app.route("/talk", methods=["POST"])
def start_talk():
    data  = request.get_json(silent=True) or {}
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "no topic"}), 400

    session_id = uuid.uuid4().hex[:10]
    q          = queue.Queue()
    stop_event = threading.Event()
    try:
        duration = int(data.get("duration") or get_room_config().get("free_talk_duration", 300))
    except (TypeError, ValueError):
        duration = 300
    duration = max(60, min(1800, duration))

    if len(talk_sessions) > 100:
        oldest = next(iter(talk_sessions))
        talk_sessions.pop(oldest, None)
        talk_stop_events.pop(oldest, None)

    talk_sessions[session_id]    = q
    talk_stop_events[session_id] = stop_event

    thread = threading.Thread(
        target=run_free_talk_thread,
        args=(topic, list(conversation_history), q, stop_event, duration),
        daemon=True
    )
    thread.start()
    return jsonify({"session_id": session_id, "duration": duration})


@app.route("/talk_stream/<session_id>")
def talk_stream(session_id):
    q = talk_sessions.get(session_id)
    if not q:
        return "Session not found", 404

    def generate():
        try:
            while True:
                try:
                    msg = q.get(timeout=180)
                except queue.Empty:
                    break
                if msg is None:
                    yield 'data: {"done": true}\n\n'
                    break
                yield f"data: {json.dumps(msg)}\n\n"
        finally:
            talk_sessions.pop(session_id, None)
            talk_stop_events.pop(session_id, None)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.route("/stop_talk/<session_id>", methods=["POST"])
def stop_talk(session_id):
    event = talk_stop_events.get(session_id)
    if event:
        event.set()
    return jsonify({"stopped": True})


if __name__ == "__main__":
    ollama_ok = check_ollama()
    models    = check_ollama_models() if ollama_ok else []
    memory    = get_memory_status()
    print_startup_banner(ollama_ok, models, memory)
    app.run(debug=False, port=5000)
