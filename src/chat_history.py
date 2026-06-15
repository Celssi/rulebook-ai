"""Chat history helpers (shared by API and domain layers)."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

MEMORY_MESSAGES = 10


def recent_chat_history(
    messages: list[dict[str, str]], max_messages: int = MEMORY_MESSAGES
) -> list[dict[str, str]]:
    return [m for m in messages[-max_messages:] if m.get("role") in {"user", "assistant"}]


def to_langchain_history(history: list[dict[str, str]]):
    out = []
    for msg in history:
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        if msg.get("role") == "user":
            out.append(HumanMessage(content=content))
        elif msg.get("role") == "assistant":
            out.append(AIMessage(content=content))
    return out
