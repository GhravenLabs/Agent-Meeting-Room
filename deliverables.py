from datetime import datetime, timezone


DELIVERABLE_TYPES = {
    "code_review": {
        "label": "Code Review Summary",
        "sections": [
            "Context",
            "Key Findings",
            "Recommended Changes",
            "Verification",
            "Follow-up Questions",
        ],
    },
    "product_memo": {
        "label": "Product Decision Memo",
        "sections": [
            "Decision",
            "Background",
            "Options Considered",
            "Trade-offs",
            "Next Steps",
        ],
    },
    "research_brief": {
        "label": "Research Brief",
        "sections": [
            "Question",
            "What We Learned",
            "Evidence",
            "Risks and Unknowns",
            "Next Research Steps",
        ],
    },
    "research_action_brief": {
        "label": "Research Action Brief",
        "sections": [
            "Decision",
            "Evidence to Use",
            "Sellable Asset",
            "Risks and Gates",
            "Next 7 Days",
        ],
    },
    "implementation_plan": {
        "label": "Implementation Plan",
        "sections": [
            "Goal",
            "Scope",
            "Steps",
            "Testing",
            "Risks",
        ],
    },
    "bug_report": {
        "label": "Bug Report",
        "sections": [
            "Summary",
            "Observed Behavior",
            "Expected Behavior",
            "Reproduction Notes",
            "Suggested Fix",
        ],
    },
    "release_notes": {
        "label": "Release Notes Draft",
        "sections": [
            "Highlights",
            "Added",
            "Changed",
            "Fixed",
            "Verification",
        ],
    },
    "github_issue": {
        "label": "GitHub Issue Draft",
        "sections": [
            "Problem",
            "Why It Matters",
            "Proposed Solution",
            "Acceptance Criteria",
            "Extra Context",
        ],
    },
    "pull_request": {
        "label": "Pull Request Description",
        "sections": [
            "Problem",
            "What Changed",
            "Before and After",
            "Verification",
            "Notes for Reviewers",
        ],
    },
}


def deliverable_options() -> list:
    return [
        {"key": key, "label": config["label"]}
        for key, config in DELIVERABLE_TYPES.items()
    ]


def _clean_text(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def _message_excerpt(message: dict, limit: int = 220) -> str:
    role = _clean_text(message.get("role", "Unknown")) or "Unknown"
    content = _clean_text(message.get("content", ""))
    if len(content) > limit:
        content = f"{content[:limit - 3].rstrip()}..."
    return f"**{role}:** {content}" if content else f"**{role}:** _No content_"


def _participant_line(messages: list) -> str:
    participants = []
    seen = set()
    for message in messages:
        role = _clean_text(message.get("role", "Unknown")) or "Unknown"
        key = role.lower()
        if key not in seen:
            seen.add(key)
            participants.append(role)
    return ", ".join(participants) if participants else "No participants yet"


def _conversation_bullets(messages: list, limit: int = 6) -> list:
    if not messages:
        return ["No meeting content yet."]
    return [_message_excerpt(message) for message in messages[-limit:]]


def _section_content(kind: str, section: str, messages: list) -> list:
    bullets = _conversation_bullets(messages)
    if section in {"Context", "Background", "Question", "Goal", "Summary", "Problem"}:
        return bullets[:3]
    if section in {"Key Findings", "What We Learned", "Observed Behavior", "Highlights"}:
        return bullets
    if section in {"Steps", "Next Steps", "Recommended Changes", "Proposed Solution", "Suggested Fix"}:
        return ["Turn the strongest points from the meeting into concrete tasks.", "Assign owners and deadlines before sharing externally."]
    if section == "Evidence to Use":
        return ["Quote or link only the claims that were actually discussed or verified.", "Separate measured proof from assumptions before publishing."]
    if section == "Sellable Asset":
        return ["Turn the research into one concrete proof asset: demo, report, SOP, checklist, lead list, or outreach script."]
    if section == "Risks and Gates":
        return ["Name privacy, accuracy, client-data, cost, and public-positioning risks before acting.", "Do not send, publish, or deploy until the required human approval gate is clear."]
    if section == "Next 7 Days":
        return ["Choose the smallest useful build or outreach step.", "Define the verification artifact that proves the step worked."]
    if section in {"Testing", "Verification"}:
        return ["Add the local commands, screenshots, or manual checks used to verify this work."]
    if section == "Acceptance Criteria":
        return ["The issue is resolved for the discussed scenario.", "The change is covered by an appropriate local verification step."]
    if section == "Before and After":
        return ["Before: capture the current behavior or limitation.", "After: explain the new behavior in plain language."]
    if section in {"Risks", "Risks and Unknowns", "Trade-offs", "Follow-up Questions"}:
        return ["Confirm assumptions that were not proven during the meeting."]
    if section == "Options Considered":
        return ["Option A: proceed with the discussed approach.", "Option B: defer until more information is available."]
    if section in {"Added", "Changed", "Fixed"}:
        return ["Summarize user-facing changes from the meeting notes."]
    if section == "Extra Context":
        return ["Link related discussions, issues, screenshots, or transcripts here."]
    if section == "Notes for Reviewers":
        return ["Mention any intentionally narrow scope or follow-up work."]
    return ["Refine this section from the meeting transcript."]


def generate_deliverable(kind: str, messages: list, room_title: str = "Agent Meeting Room") -> str:
    if kind not in DELIVERABLE_TYPES:
        raise ValueError("unknown deliverable type")

    config = DELIVERABLE_TYPES[kind]
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    title = config["label"]
    safe_room_title = _clean_text(room_title) or "Agent Meeting Room"

    lines = [
        f"# {title}",
        "",
        f"- Room: {safe_room_title}",
        f"- Generated: {generated_at}",
        f"- Participants: {_participant_line(messages)}",
        f"- Source messages: {len(messages)}",
        "",
    ]

    for section in config["sections"]:
        lines.extend([f"## {section}", ""])
        for item in _section_content(kind, section, messages):
            lines.append(f"- {item}")
        lines.append("")

    lines.extend([
        "## Source Conversation",
        "",
    ])
    if not messages:
        lines.extend(["_No messages yet._", ""])
    else:
        for index, message in enumerate(messages, start=1):
            lines.append(f"{index}. {_message_excerpt(message, limit=320)}")
        lines.append("")

    return "\n".join(lines)
