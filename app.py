from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from agents import run_agents, run_free_talk_thread
from memory import save_to_obsidian, get_recent_memory
import os
import json
import queue
import threading
import uuid
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
conversation_history = []
talk_sessions    = {}   # session_id -> queue.Queue
talk_stop_events = {}   # session_id -> threading.Event


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    data       = request.json
    user_msg   = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"error": "empty message"}), 400

    # Add user message to history
    conversation_history.append({
        "role":    "user",
        "content": user_msg
    })

    # Get recent memory context
    memory_context = get_recent_memory()

    # Run agents based on mentions
    responses = run_agents(
        user_msg,
        conversation_history,
        memory_context
    )

    # Add responses to history
    for r in responses:
        conversation_history.append({
            "role":    r["agent"],
            "content": r["message"]
        })

    # Keep history manageable
    if len(conversation_history) > 50:
        conversation_history.pop(0)

    return jsonify({"responses": responses})


@app.route("/save_memory", methods=["POST"])
def save_memory():
    data    = request.json
    content = data.get("content", "")
    title   = data.get("title", "Meeting note")
    result  = save_to_obsidian(title, content)
    return jsonify({"saved": result})


@app.route("/clear", methods=["POST"])
def clear():
    conversation_history.clear()
    return jsonify({"cleared": True})


@app.route("/talk", methods=["POST"])
def start_talk():
    data  = request.json
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "no topic"}), 400

    session_id = uuid.uuid4().hex[:10]
    q          = queue.Queue()
    stop_event = threading.Event()

    # Evict oldest session if map grows too large (prevents memory leak on abandoned sessions)
    if len(talk_sessions) > 100:
        oldest = next(iter(talk_sessions))
        talk_sessions.pop(oldest, None)
        talk_stop_events.pop(oldest, None)
    talk_sessions[session_id]    = q
    talk_stop_events[session_id] = stop_event

    thread = threading.Thread(
        target=run_free_talk_thread,
        args=(topic, list(conversation_history), q, stop_event),
        daemon=True
    )
    thread.start()

    return jsonify({"session_id": session_id})


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
                    yield "data: {\"done\": true}\n\n"
                    break
                yield f"data: {json.dumps(msg)}\n\n"
        finally:
            talk_sessions.pop(session_id, None)
            talk_stop_events.pop(session_id, None)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/stop_talk/<session_id>", methods=["POST"])
def stop_talk(session_id):
    event = talk_stop_events.get(session_id)
    if event:
        event.set()
    return jsonify({"stopped": True})


if __name__ == "__main__":
    print("=" * 45)
    print("  Agent Meeting Room starting...")
    print("  Open: http://localhost:5000")
    print("=" * 45)
    app.run(debug=False, port=5000)