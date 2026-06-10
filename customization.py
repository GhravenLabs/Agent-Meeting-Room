import copy
import json
import os
from pathlib import Path

from agents import AGENTS


CONFIG_PATH = Path(os.getenv(
    "AGENT_PROFILES_PATH",
    Path(__file__).with_name("agent_profiles.json"),
))

DEFAULT_ROOM = {
    "title": "Agent Meeting Room",
    "subtitle": "4 local AI agents + cloud AI on demand",
    "logo": "",
    "purpose": "",
    "free_talk_duration": 300,
    "response_word_limit": 150,
    "tts_enabled": False,
}

DEFAULT_PRESETS = {
    "default": {
        "name": "Default Room",
        "description": "Balanced general-purpose local agent table.",
        "agents": ["mistral", "phi3", "gemma2", "deepseek"],
    },
    "code_review": {
        "name": "Code Review",
        "description": "Practical review with analysis, edge cases, and summary.",
        "agents": ["mistral", "deepseek", "gemma2"],
        "prompt": "@all review this code for bugs, edge cases, and missing tests:\n\n",
    },
    "product_debate": {
        "name": "Product Debate",
        "description": "Compare tradeoffs, risks, and product decisions from multiple angles.",
        "agents": ["mistral", "phi3", "deepseek", "gemma2"],
        "prompt": "@debate product decision: should we build this feature now or wait?\n\nContext:\n",
    },
    "research": {
        "name": "Research",
        "description": "Map options, assumptions, unknowns, and next investigation steps.",
        "agents": ["mistral", "gemma2", "deepseek"],
        "prompt": "@all research this topic and return key facts, risks, and next steps:\n\n",
    },
    "planning": {
        "name": "Planning",
        "description": "Turn a goal into a scoped implementation plan and checklist.",
        "agents": ["mistral", "phi3", "gemma2"],
        "prompt": "@all turn this goal into a practical implementation plan:\n\n",
    },
    "debate_panel": {
        "name": "Debate Panel",
        "description": "Contrasting viewpoints with final synthesis.",
        "agents": ["mistral", "phi3", "deepseek", "gemma2"],
        "prompt": "@debate ",
    },
}


def clamp_free_talk_duration(value, default=300):
    """Clamp Free Talk duration to the supported 1-30 minute range."""
    try:
        return max(60, min(1800, int(value)))
    except (TypeError, ValueError):
        return default


def clamp_response_word_limit(value, default=150):
    """Clamp agent replies to the supported 50-500 word range."""
    try:
        return max(50, min(500, int(value)))
    except (TypeError, ValueError):
        return default


def default_agent_profile(key, agent):
    return {
        "key": key,
        "mention": f"@{key}",
        "model": agent["model"],
        "name": agent["name"],
        "display_name": agent["name"],
        "color": agent["color"],
        "avatar": "",
        "role": "",
        "tone": "",
        "expertise": "",
        "behavior": "",
        "personality": agent["personality"],
        "voice": "",
        "enabled": True,
    }


def default_config():
    return {
        "room": copy.deepcopy(DEFAULT_ROOM),
        "agents": {key: default_agent_profile(key, agent) for key, agent in AGENTS.items()},
        "presets": copy.deepcopy(DEFAULT_PRESETS),
        "active_preset": "default",
    }


def _merge_agent_profile(key, saved):
    base = default_agent_profile(key, AGENTS[key])
    if isinstance(saved, dict):
        for field in base:
            if field in saved and saved[field] is not None:
                base[field] = saved[field]
    base["key"] = key
    base["mention"] = f"@{key}"
    base["model"] = AGENTS[key]["model"]
    return base


def normalize_config(raw):
    config = default_config()
    if not isinstance(raw, dict):
        return config

    room = raw.get("room")
    if isinstance(room, dict):
        config["room"].update({k: v for k, v in room.items() if k in config["room"]})
    config["room"]["free_talk_duration"] = clamp_free_talk_duration(
        config["room"].get("free_talk_duration", 300)
    )
    config["room"]["response_word_limit"] = clamp_response_word_limit(
        config["room"].get("response_word_limit", 150)
    )
    config["room"]["tts_enabled"] = bool(config["room"].get("tts_enabled", False))

    saved_agents = raw.get("agents", {})
    if isinstance(saved_agents, dict):
        for key in AGENTS:
            config["agents"][key] = _merge_agent_profile(key, saved_agents.get(key, {}))

    presets = raw.get("presets")
    if isinstance(presets, dict):
        for key, preset in presets.items():
            if not isinstance(preset, dict):
                continue
            agents = preset.get("agents", [])
            if not isinstance(agents, list):
                agents = []
            config["presets"][key] = {
                "name": str(preset.get("name") or key),
                "description": str(preset.get("description") or ""),
                "agents": [agent for agent in agents if agent in AGENTS],
                "prompt": str(
                    preset.get("prompt")
                    if "prompt" in preset
                    else config["presets"].get(key, {}).get("prompt", "")
                ),
            }

    active_preset = raw.get("active_preset")
    if isinstance(active_preset, str) and active_preset in config["presets"]:
        config["active_preset"] = active_preset

    return config


def load_config():
    if not CONFIG_PATH.exists():
        return default_config()
    try:
        return normalize_config(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError):
        return default_config()


def save_config(config):
    normalized = normalize_config(config)
    CONFIG_PATH.write_text(
        json.dumps(normalized, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return normalized


def get_agent_profiles():
    return load_config()["agents"]


def get_room_config():
    return load_config()["room"]


def get_effective_agents():
    profiles = get_agent_profiles()
    effective = {}
    for key, agent in AGENTS.items():
        profile = profiles[key]
        personality_parts = [profile.get("personality") or agent["personality"]]
        extras = []
        if profile.get("role"):
            extras.append(f"Role: {profile['role']}")
        if profile.get("tone"):
            extras.append(f"Tone: {profile['tone']}")
        if profile.get("expertise"):
            extras.append(f"Expertise: {profile['expertise']}")
        if profile.get("behavior"):
            extras.append(f"Meeting behavior: {profile['behavior']}")
        if extras:
            personality_parts.append("\n".join(extras))

        effective[key] = {
            **agent,
            "name": profile.get("display_name") or profile.get("name") or agent["name"],
            "color": profile.get("color") or agent["color"],
            "personality": "\n\n".join(personality_parts),
            "avatar": profile.get("avatar", ""),
            "voice": profile.get("voice", ""),
            "enabled": bool(profile.get("enabled", True)),
        }
    return effective
