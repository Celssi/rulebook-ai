"""Factory for GM solo agent multi nodes."""

from __future__ import annotations

from src.games.saves import get_play_store
from src.games.saves.context import load_play_context_from_disk


def build_multi_node(game_id: str, shortcut_ids: frozenset[str], run_shortcut_fn):
    def multi_node(state: dict) -> dict:
        shortcut_id = state.get("shortcut_id") or ""
        retrieval_cfg = state.get("retrieval") or {}
        char_id = state.get("char_id")
        chat_provider = state.get("chat_provider", "ollama")
        store = get_play_store(game_id)

        if not store or not char_id or shortcut_id not in shortcut_ids:
            return {
                "tool_output": f"Unknown or unavailable shortcut: {shortcut_id}",
                "sources": [],
                "language": "en",
            }

        ctx = load_play_context_from_disk(store, char_id)
        user_message, answer, sources, _route = run_shortcut_fn(
            ctx,
            shortcut_id,
            chat_provider=chat_provider,
            retrieval_cfg=retrieval_cfg,
            top_k=10,
            factions=[],
        )
        store.persist_ctx(ctx)
        if answer.strip() == user_message.strip() or answer.startswith(user_message):
            tool_output = answer
        else:
            tool_output = f"{user_message}\n\n{answer}"
        return {
            "tool_output": tool_output,
            "sources": sources,
            "language": "en",
            "play_entity": ctx.entity,
        }

    return multi_node
