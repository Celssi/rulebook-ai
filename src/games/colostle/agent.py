"""Colostle agent graph node."""

from __future__ import annotations

from src.games.colostle.actions import SHORTCUT_IDS
from src.games.saves import get_play_store
from src.games.saves.context import load_play_context_from_disk

GAME_COLOSTLE = "colostle"


def _shortcut_tool_output(user_message: str, answer: str) -> str:
    if answer.strip() == user_message.strip():
        return answer
    if answer.startswith(user_message):
        return answer
    return f"{user_message}\n\n{answer}"


def colostle_multi_node(state: dict) -> dict:
    game_id = state.get("game_id", GAME_COLOSTLE)
    shortcut_id = state.get("shortcut_id") or "rules_help"
    retrieval_cfg = state.get("retrieval") or {}
    char_id = state.get("char_id")
    chat_provider = state.get("chat_provider", "ollama")
    store = get_play_store(game_id)

    if not store or not char_id or shortcut_id not in SHORTCUT_IDS:
        return {
            "tool_output": f"Unknown or unavailable shortcut: {shortcut_id}",
            "sources": [],
            "language": "en",
        }

    from src.games.colostle.play_handlers import run_character_shortcut

    ctx = load_play_context_from_disk(store, char_id)
    user_message, answer, sources, _route = run_character_shortcut(
        ctx,
        shortcut_id,
        chat_provider=chat_provider,
        retrieval_cfg=retrieval_cfg,
        top_k=10,
        factions=[],
    )
    store.persist_ctx(ctx)
    return {
        "tool_output": _shortcut_tool_output(user_message, answer),
        "sources": sources,
        "language": "en",
        "play_entity": ctx.entity,
    }
