"""System prompts and language handling (English-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.config import DEFAULT_GAME_ID, GAME_BRAMBLETREK

if TYPE_CHECKING:
    from src.brambletrek_character import BrambletrekCharacter
    from src.game_state import GameState


def detect_language(question: str) -> str:
    """Return language code. Project is English-only."""
    _ = question
    return "en"


def build_system_prompt(
    language: str,
    game: "GameState | None" = None,
    game_id: str = DEFAULT_GAME_ID,
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> str:
    from src.game_state import format_for_prompt

    _ = language
    lang_instruction = "Answer in English."
    if game_id == GAME_BRAMBLETREK:
        from src.brambletrek_character import format_for_prompt as format_character

        char_block = format_character(brambletrek_character)
        char_section = f"\n\n{char_block}" if char_block else ""
        return f"""You are a Brambletrek rules assistant for personal study and tabletop play.

{lang_instruction}
{char_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say it clearly and do not invent rules.
- When the user asks about dice results, explain what the rolled values mean according to the cited rules text.
- When tool output includes a dice roll or drawn card, treat it as a live table event: state the numbers/cards clearly, then explain rules from context if relevant.
- When a Gnawborn character sheet is provided, reference their current Health, Morale, and Supplies when explaining event outcomes.
- Do not invent rules or card/dice outcomes beyond what the tool output and context provide.
- Keep answers concise and practical for a game facilitator.
- When citing rules, mention source file and page number from the provided metadata.
"""

    game_block = format_for_prompt(game, "en")
    game_section = f"\n\n{game_block}" if game_block else ""
    return f"""You are a Warhammer 40,000 rules assistant for personal study and casual games.

{lang_instruction}
{game_section}

Rules:
- Answer ONLY using the provided context excerpts. If the context does not contain enough information, say clearly that it was not found in the documents (do not guess rules).
- When tool output includes a dice roll or drawn card, present that result as a live table event, then tie rule explanations to the cited excerpts only.
- Do not invent rules, dice results, or cards beyond tool output and retrieved context.
- When citing rules, mention the source file and page number from the context metadata.
- Be concise and practical for players at the table.
"""


def tool_output_instructions(route: str) -> str:
    """Extra synthesis guidance when combining tools with rules."""
    if route in {"dice", "cards"}:
        return (
            "The tool result is authoritative for rolls/cards. "
            "Do not change the numbers or card names."
        )
    if route == "card_rag":
        return (
            "The drawn card in the tool result is authoritative. "
            "Explain its meaning using only the cited rule excerpts; do not invent table rows."
        )
    return ""


def format_context_block(nodes: list) -> str:
    """Format retrieved nodes for the LLM prompt."""
    parts: list[str] = []
    for i, node in enumerate(nodes, 1):
        meta = node.metadata or {}
        source = meta.get("source_label") or meta.get("source_file", "unknown")
        page = meta.get("page", "?")
        faction = meta.get("faction", "")
        header = f"[{i}] {source} (page {page}, faction={faction})"
        parts.append(f"{header}\n{node.get_content()}")
    return "\n\n---\n\n".join(parts)
