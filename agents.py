import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

AGENTS = {
    "mistral": {
        "model":       "mistral",
        "name":        "Mistral",
        "color":       "#378ADD",
        "personality": """You are Mistral, a sharp analytical thinker. 
You give direct, well-reasoned answers. You back up opinions with logic.
You are honest when you disagree with others. Keep responses concise — 
under 150 words unless asked for detail. You are in a group meeting 
with other AI agents."""
    },
    "phi3": {
        "model":       "phi3",
        "name":        "Phi3",
        "color":       "#1D9E75",
        "personality": """You are Phi3, a creative and lateral thinker.
You look for angles others miss. You ask good questions and challenge 
assumptions. You are concise and practical. Keep responses under 150 words 
unless asked for detail. You are in a group meeting with other AI agents."""
    },
    "gemma2": {
        "model":       "gemma2:2b",
        "name":        "Gemma2",
        "color":       "#7F77DD",
        "personality": """You are Gemma2, a careful and balanced thinker.
You weigh all sides before concluding. You are good at summarizing complex
ideas simply. You look for common ground. Keep responses under 150 words
unless asked for detail. You are in a group meeting with other AI agents."""
    },
    "deepseek": {
        "model":       "deepseek-r1:7b",
        "name":        "DeepSeek",
        "color":       "#E05C5C",
        "personality": """You are DeepSeek, a deep reasoning thinker.
You excel at step-by-step logical analysis and thorough problem solving.
You are methodical and precise. Keep responses under 150 words unless
asked for detail. You are in a group meeting with other AI agents."""
    }
}

CLAUDE_MODEL = "claude-sonnet-4-6"


def build_context(conversation_history, memory_context=""):
    """Build conversation context string for agents."""
    context = ""
    if memory_context:
        context += f"MEMORY FROM PAST MEETINGS:\n{memory_context}\n\n"
    if conversation_history:
        context += "RECENT CONVERSATION:\n"
        for msg in conversation_history[-10:]:
            role = msg["role"].upper()
            context += f"{role}: {msg['content']}\n"
    return context


def ask_ollama(model, system_prompt, user_message, context=""):
    """Ask a local Ollama model."""
    full_prompt = ""
    if context:
        full_prompt += f"{context}\n\n"
    full_prompt += f"User message: {user_message}\n\nYour response:"

    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model":      model,
                "system":     system_prompt,
                "prompt":     full_prompt,
                "stream":     False,
                "keep_alive": 0
            },
            timeout=120
        )
        return response.json()["response"].strip()
    except Exception as e:
        return f"[Error: {e}]"


def ask_claude(message, context=""):
    """Ask Claude API."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return "Claude API key not set in .env file."

    system = """You are Claude, a highly capable AI assistant 
joining a meeting with other AI agents. You give thoughtful, 
nuanced responses. You are the most capable agent in the room 
but you are collaborative not domineering. Be concise unless 
asked for detail."""

    full_message = ""
    if context:
        full_message += f"{context}\n\n"
    full_message += f"User message: {message}"

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key":         api_key,
                "anthropic-version": "2023-06-01",
                "content-type":      "application/json"
            },
            json={
                "model":      CLAUDE_MODEL,
                "max_tokens": 500,
                "system":     system,
                "messages":   [{"role": "user", "content": full_message}]
            },
            timeout=30
        )
        return response.json()["content"][0]["text"].strip()
    except Exception as e:
        return f"[Claude error: {e}]"


def run_debate(message, conversation_history, memory_context):
    """
    Full auto-debate mode.
    Round 1: All 3 agents answer independently.
    Round 2: Each agent responds to the others.
    Round 3: Summary of consensus or disagreement.
    """
    responses = []
    context   = build_context(conversation_history, memory_context)

    # Round 1 — Independent answers
    round1 = {}
    for key, agent in AGENTS.items():
        print(f"[Debate] Round 1 — asking {agent['name']}...")
        answer = ask_ollama(
            agent["model"],
            agent["personality"],
            message,
            context
        )
        round1[key] = answer
        responses.append({
            "agent":   agent["name"],
            "model":   key,
            "color":   agent["color"],
            "message": answer,
            "round":   1
        })

    # Build Round 1 summary for Round 2
    round1_summary = "\n\n".join([
        f"{AGENTS[k]['name']} said: {v}"
        for k, v in round1.items()
    ])

    # Round 2 — Each agent reacts to others
    for key, agent in AGENTS.items():
        others = {k: v for k, v in round1.items() if k != key}
        others_text = "\n".join([
            f"{AGENTS[k]['name']}: {v}"
            for k, v in others.items()
        ])

        debate_prompt = f"""The original question was: {message}

You already said: {round1[key]}

The other agents responded:
{others_text}

Do you agree, disagree, or want to add something? 
Be direct and concise — under 100 words."""

        print(f"[Debate] Round 2 — asking {agent['name']}...")
        reaction = ask_ollama(
            agent["model"],
            agent["personality"],
            debate_prompt,
            ""
        )
        responses.append({
            "agent":   agent["name"],
            "model":   key,
            "color":   agent["color"],
            "message": reaction,
            "round":   2
        })

    # Round 3 — Gemma2 summarizes consensus
    summary_prompt = f"""You just had this debate:

Original question: {message}

{round1_summary}

Summarize in 2-3 sentences:
1. What did the group agree on?
2. What did they disagree on?
3. What is the best answer based on the discussion?"""

    print(f"[Debate] Round 3 — summarizing...")
    summary = ask_ollama(
        "gemma2:2b",
        AGENTS["gemma2"]["personality"],
        summary_prompt,
        ""
    )
    responses.append({
        "agent":   "Summary",
        "model":   "summary",
        "color":   "#BA7517",
        "message": summary,
        "round":   3
    })

    return responses


def run_agents(message, conversation_history, memory_context=""):
    """
    Parse mentions and route to correct agents.
    @all      — all 3 local agents respond
    @debate   — full auto-debate with rounds
    @mistral  — only Mistral responds
    @phi3     — only Phi3 responds
    @gemma2   — only Gemma2 responds
    @deepseek — only DeepSeek responds
    @claude   — only Claude API responds
    No mention — defaults to @all
    """
    msg_lower = message.lower()
    context   = build_context(conversation_history, memory_context)
    responses = []

    # Debate mode
    if "@debate" in msg_lower:
        clean_msg = message.replace("@debate", "").strip()
        return run_debate(clean_msg, conversation_history, memory_context)

    # Claude only
    if "@claude" in msg_lower:
        clean_msg = message.replace("@claude", "").strip()
        print(f"[Agents] Asking Claude...")
        reply = ask_claude(clean_msg, context)
        return [{
            "agent":   "Claude",
            "model":   "claude",
            "color":   "#534AB7",
            "message": reply,
            "round":   1
        }]

    # Specific agent mentions
    mentioned = []
    for key in AGENTS:
        if f"@{key}" in msg_lower:
            mentioned.append(key)

    # @all or no mention = all agents
    if "@all" in msg_lower or not mentioned:
        mentioned = list(AGENTS.keys())

    # Clean message of all mentions
    clean_msg = message
    for key in AGENTS:
        clean_msg = clean_msg.replace(f"@{key}", "")
    clean_msg = clean_msg.replace("@all", "").strip()

    # Ask each mentioned agent
    for key in mentioned:
        agent = AGENTS[key]
        print(f"[Agents] Asking {agent['name']}...")
        reply = ask_ollama(
            agent["model"],
            agent["personality"],
            clean_msg,
            context
        )
        responses.append({
            "agent":   agent["name"],
            "model":   key,
            "color":   agent["color"],
            "message": reply,
            "round":   1
        })

    return responses


def run_free_talk_thread(topic, conversation_history, output_queue, stop_event, duration=None):
    """
    Run all local agents in a free-flowing conversation for `duration` seconds.
    Each agent takes turns responding to the group.
    Results are pushed into output_queue as they arrive.
    A None sentinel is pushed when finished.
    """
    if duration is None:
        import os as _os
        duration = int(_os.getenv("FREE_TALK_DURATION", "300"))
    start_time = time.time()
    talk_history = []
    agent_keys = list(AGENTS.keys())
    initial_context = build_context(conversation_history)
    turn = 0

    while not stop_event.is_set() and (time.time() - start_time) < duration:
        key = agent_keys[turn % len(agent_keys)]
        agent = AGENTS[key]

        if talk_history:
            talk_context = "DISCUSSION SO FAR:\n" + "\n".join(
                f"{e['name']}: {e['message']}" for e in talk_history[-8:]
            )
        else:
            talk_context = ""

        prompt = f"""You are in a free-flowing group discussion about: "{topic}"

{talk_context}

It's your turn to speak. React to what others said, share your view,
or ask a question. Address agents by name if responding to them.
Keep it under 80 words. Be conversational, not formal."""

        print(f"[Talk] Turn {turn + 1} — {agent['name']}...")
        reply = ask_ollama(
            agent["model"],
            agent["personality"],
            prompt,
            initial_context if turn == 0 else ""
        )

        if stop_event.is_set():
            break

        entry = {
            "agent":   agent["name"],
            "model":   key,
            "color":   agent["color"],
            "message": reply,
            "round":   1,
            "elapsed": int(time.time() - start_time)
        }
        talk_history.append({"name": agent["name"], "message": reply})
        output_queue.put(entry)
        turn += 1

    if not talk_history:
        output_queue.put(None)
        return

    # Summary round (~30s)
    print("[Talk] Generating summary...")
    full_transcript = "\n".join(
        f"{e['name']}: {e['message']}" for e in talk_history
    )
    summary_prompt = f"""The agents just had a free discussion about: "{topic}"

Full conversation:
{full_transcript}

Write a concise summary (3-5 sentences) covering:
1. The main points raised
2. Where agents agreed or disagreed
3. The key insight or conclusion from the discussion"""

    summary = ask_ollama(
        "gemma2:2b",
        AGENTS["gemma2"]["personality"],
        summary_prompt,
        ""
    )

    output_queue.put({
        "agent":      "Summary",
        "model":      "summary",
        "color":      "#BA7517",
        "message":    summary,
        "round":      3,
        "is_summary": True
    })
    output_queue.put(None)  # sentinel — stream is done