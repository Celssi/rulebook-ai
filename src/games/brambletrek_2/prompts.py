"""Brambletrek 2 system prompt fragment."""

from __future__ import annotations

from src.games.brambletrek_2.character import Brambletrek2Character, format_for_prompt as format_character


def brambletrek_2_system_prompt(
    *,
    language_instruction: str,
    character: Brambletrek2Character | None,
    story_mode: str,
    card_source: str,
) -> str:
    char_block = format_character(
        character,
        story_mode=story_mode,
        card_source=card_source,
    )
    char_section = f"\n\n{char_block}" if char_block else ""
    story_rules = (
        "- In **ai_narrator** story mode: after resolving mechanics, add brief in-world prose.\n"
        if story_mode == "ai_narrator"
        else "- In **player** story mode: explain rules and mechanics; the player writes the journal.\n"
    )
    card_rules = (
        "- **Physical deck** mode: do not auto-draw; user reports pulls.\n"
        if card_source == "physical"
        else "- **Virtual deck** mode: tool draws are authoritative.\n"
    )
    hollow_note = ""
    if character and character.in_hollow:
        hollow_note = (
            "- Player is in the **Misty Hollow** grid — reference hollow tables and memory fragments.\n"
        )
    return f"""You are a Brambletrek 2 rules assistant for the Hundred Acre Woods solo RPG.

{language_instruction}
{char_section}

Rules:
- Answer ONLY using provided context. Stat max is 30 per resource.
- Exploration: 4 cards/day; red (hearts/diamonds) favourable, black unfortunate.
- Combat: opponent by rank, initiative, 4 tactic cards per legacy.
- Misty Hollow: memory fragments, 5×4 grid navigation, escape test.
{hollow_note}{story_rules}{card_rules}- Lonelog: d: draws, => narrator, @ hollow moves.
- Cite source file and page from metadata when possible.
"""
