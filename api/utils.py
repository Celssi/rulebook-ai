"""Shared chat/history helpers for API (no Streamlit)."""

from __future__ import annotations

from src.chat_history import MEMORY_MESSAGES, recent_chat_history, to_langchain_history
from src.retrieval_profiles import (
    DEFAULT_RETRIEVAL_PROFILE,
    RETRIEVAL_PROFILES,
    resolve_retrieval_profile,
)

FACTION_LABELS = {
    "core": "Core / Quickstart",
    "space_marines": "Codex: Space Marines",
    "tyranids": "Codex: Tyranids",
    "cards_sm": "SM Datasheets",
    "cards_nids": "Tyranid Datasheets",
    "supplement": "Supplement",
    "adventure": "Adventure",
}
