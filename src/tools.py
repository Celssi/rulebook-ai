"""Tools for the LangGraph agent."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml

from src.config import DEFAULT_GAME_ID, LEVIATHAN_YAML
from src.game_state import GameState
from src.play_tools import (
    CardToolResult,
    DiceRollResult,
    clear_deck_store,
    deck_remaining,
    draw_cards,
    extract_dice_expression,
    format_card_result,
    format_dice_result,
    get_deck_snapshot,
    is_card_plus_rules_question,
    is_card_question,
    is_dice_question,
    parse_dice_expression,
    parse_explicit_command,
    reset_deck,
    roll_dice,
    run_explicit_command,
    sync_deck_store,
)
from src.rag import query as rag_query

__all__ = [
    "CardToolResult",
    "DiceRollResult",
    "clear_deck_store",
    "deck_remaining",
    "draw_cards",
    "extract_dice_expression",
    "format_card_result",
    "format_dice_result",
    "get_deck_snapshot",
    "is_card_plus_rules_question",
    "is_card_question",
    "is_dice_question",
    "is_leviathan_list_question",
    "list_leviathan_units",
    "parse_dice_expression",
    "parse_explicit_command",
    "reset_deck",
    "roll_dice",
    "run_explicit_command",
    "search_rules",
    "sync_deck_store",
]


def list_leviathan_units(
    side: Literal["space_marines", "tyranids", "both"] = "both",
) -> str:
    """Return curated Leviathan box unit lists from YAML."""
    if not LEVIATHAN_YAML.exists():
        return "Leviathan unit list not found (missing data/curated/leviathan_units.yaml)."

    data = yaml.safe_load(LEVIATHAN_YAML.read_text(encoding="utf-8"))
    lines: list[str] = [f"Box: {data.get('box', 'Leviathan')} ({data.get('edition', '')})"]

    sides = ["space_marines", "tyranids"] if side == "both" else [side]
    for key in sides:
        block = data.get(key, {})
        faction = block.get("faction", key)
        lines.append(f"\n## {faction}")
        for u in block.get("units", []):
            role = u.get("role", "")
            notes = u.get("notes", "")
            lines.append(f"- **{u['name']}** ({role}): {notes}")

    return "\n".join(lines)


def search_rules(
    query: str,
    factions: list[str] | None = None,
    top_k: int = 5,
    game_state: GameState | None = None,
    game_id: str = DEFAULT_GAME_ID,
    candidate_k: int | None = None,
    use_hybrid: bool = True,
    chat_history: list[dict[str, str]] | None = None,
    brambletrek_character=None,
) -> dict:
    """RAG search over indexed PDFs."""
    result = rag_query(
        query,
        top_k=max(top_k, 8),
        factions=factions or None,
        game_state=game_state,
        game_id=game_id,
        candidate_k=candidate_k,
        use_hybrid=use_hybrid,
        chat_history=chat_history,
        brambletrek_character=brambletrek_character,
    )
    return {
        "answer": result.answer,
        "sources": result.sources,
        "language": result.language,
    }


def is_leviathan_list_question(text: str) -> bool:
    lower = text.lower()
    keywords = [
        "leviathan",
        "box",
        "what units",
        "unit list",
        "starter",
    ]
    return any(k in lower for k in keywords)
