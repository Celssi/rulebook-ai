"""Persist UI settings (game + RAG) across browser refresh and server restarts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.saves.storage import SAVES_ROOT, read_json, write_json

if TYPE_CHECKING:
    from src.games.saves.context import AppSession

PREFS_PATH = SAVES_ROOT / "ui_preferences.json"


def load_ui_preferences() -> dict:
    data = read_json(PREFS_PATH)
    return data if isinstance(data, dict) else {}


def save_ui_preferences(app: AppSession) -> None:
    write_json(
        PREFS_PATH,
        {
            "selected_game_id": app.selected_game_id,
            "chat_provider": app.chat_provider,
            "mode": app.mode,
            "top_k": app.top_k,
            "retrieval_profile": app.retrieval_profile,
            "selected_factions": app.selected_factions,
        },
    )


def apply_ui_preferences(app: AppSession) -> None:
    prefs = load_ui_preferences()
    if not prefs:
        return
    gid = prefs.get("selected_game_id")
    if isinstance(gid, str) and gid:
        app.selected_game_id = gid
    provider = prefs.get("chat_provider")
    if isinstance(provider, str) and provider in ("ollama", "claude"):
        app.chat_provider = provider  # type: ignore[assignment]
    mode = prefs.get("mode")
    if isinstance(mode, str) and mode in ("RAG", "Agent"):
        app.mode = mode
    top_k = prefs.get("top_k")
    if isinstance(top_k, int) and 3 <= top_k <= 12:
        app.top_k = top_k
    profile = prefs.get("retrieval_profile")
    if isinstance(profile, str):
        from api.utils import resolve_retrieval_profile

        app.retrieval_profile, _ = resolve_retrieval_profile(profile)
    factions = prefs.get("selected_factions")
    if factions is None or isinstance(factions, list):
        app.selected_factions = factions
