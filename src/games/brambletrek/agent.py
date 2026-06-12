"""Brambletrek agent graph nodes."""

from __future__ import annotations

from src.games.brambletrek.actions import run_shortcut
from src.games.brambletrek.character import character_from_dict
GAME_BRAMBLETREK = "brambletrek"
from src.tools import search_rules


def _format_sources(sources: list[dict], limit: int = 5) -> str:
    return "\n".join(
        f"- {s.get('source_label')} p.{s.get('page')} ({s.get('faction')})"
        for s in sources[:limit]
    )


def brambletrek_multi_node(state: dict) -> dict:
    """Pre-draw cards for a Brambletrek shortcut, then look up table meanings."""
    from langchain_core.messages import HumanMessage

    game_id = state.get("game_id", GAME_BRAMBLETREK)
    shortcut_id = state.get("shortcut_id") or "journey_day"
    retrieval_cfg = state.get("retrieval") or {}

    text = ""
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            text = msg.content if isinstance(msg.content, str) else str(msg.content)
            break

    data = state.get("brambletrek_character")
    bt = character_from_dict(data) if data else None

    run = run_shortcut(
        shortcut_id,
        game_id=game_id,
        in_aldwund=bool(bt and bt.in_aldwund),
        reason_band=bt.reason_band if bt else "",
        active_adventure=bt.active_adventure if bt else "",
        char_id=state.get("char_id"),
        card_source=state.get("card_source", "virtual"),
    )
    if shortcut_id in ("journey_day", "aldwund_day"):
        top_k = 12
    elif shortcut_id == "adventure_scene":
        top_k = 14
    else:
        top_k = 10
    result = search_rules(
        run["prompt"],
        game_state=state.get("game_state"),
        game_id=game_id,
        top_k=top_k,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=bool(retrieval_cfg.get("use_hybrid", True)),
        brambletrek_character=bt,
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
