"""Brambletrek 2 agent graph nodes."""

from __future__ import annotations

from langchain_core.messages import HumanMessage

from src.games.brambletrek_2.actions import run_shortcut
from src.games.brambletrek_2.character import character_from_dict
from src.games.brambletrek_2.play_handlers import execute_shortcut, shortcut_kwargs
from src.games.saves import AppSession
from src.tools import search_rules

GAME_BRAMBLETREK_2 = "brambletrek_2"


def _format_sources(sources: list[dict], limit: int = 5) -> str:
    return "\n".join(
        f"- {s.get('source_label')} p.{s.get('page')} ({s.get('faction')})"
        for s in sources[:limit]
    )


def brambletrek_2_multi_node(state: dict) -> dict:
    shortcut_id = state.get("shortcut_id") or "exploration_day"
    retrieval_cfg = state.get("retrieval") or {}
    data = state.get("play_entity")
    char = character_from_dict(data) if data else None

    run = run_shortcut(
        shortcut_id,
        game_id=GAME_BRAMBLETREK_2,
        legacy=char.legacy if char else "",
        char_id=state.get("char_id"),
        card_source=state.get("card_source", "virtual"),
        in_hollow=bool(char and char.in_hollow),
    )
    top_k = 12 if shortcut_id == "exploration_day" else 10
    result = search_rules(
        run["prompt"],
        game_state=state.get("game_state"),
        game_id=GAME_BRAMBLETREK_2,
        top_k=top_k,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=bool(retrieval_cfg.get("use_hybrid", True)),
        use_rerank=bool(retrieval_cfg.get("use_rerank", False)),
        play_entity=data,
        chat_provider=state.get("chat_provider", "ollama"),
    )
    source_summary = _format_sources(result["sources"])
    tool_output = (
        f"{run['user_message']}\n\n{result['answer']}\n\nSources:\n{source_summary}"
    )
    return {
        "tool_output": tool_output,
        "sources": result["sources"],
        "language": result["language"],
    }
