"""Shared chat/history helpers for API (no Streamlit)."""

from __future__ import annotations

from langchain_core.messages import AIMessage, HumanMessage

MEMORY_MESSAGES = 10

RETRIEVAL_PROFILES = {
    "Fast": {"candidate_k": 14, "use_hybrid": False, "use_rerank": False},
    "Balanced": {"candidate_k": 24, "use_hybrid": True, "use_rerank": False},
    "Quality": {"candidate_k": 70, "use_hybrid": True, "use_rerank": False},
    "Quality+ rerank": {"candidate_k": 70, "use_hybrid": True, "use_rerank": True},
}

DEFAULT_RETRIEVAL_PROFILE = "Fast"


def resolve_retrieval_profile(name: str | None) -> tuple[str, dict]:
    """Return a valid profile name and config, falling back to Fast."""
    if name in RETRIEVAL_PROFILES:
        return name, RETRIEVAL_PROFILES[name]
    return DEFAULT_RETRIEVAL_PROFILE, RETRIEVAL_PROFILES[DEFAULT_RETRIEVAL_PROFILE]

FACTION_LABELS = {
    "core": "Core / Quickstart",
    "space_marines": "Codex: Space Marines",
    "tyranids": "Codex: Tyranids",
    "cards_sm": "SM Datasheets",
    "cards_nids": "Tyranid Datasheets",
    "supplement": "Supplement",
    "adventure": "Adventure",
}


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
