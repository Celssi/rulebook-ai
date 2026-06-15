"""Shared system-prompt fragments for GM-led solo play."""

from __future__ import annotations


def story_mode_rules(*, story_mode: str, gm_role: str = "Game Master") -> str:
    if story_mode == "ai_narrator":
        return (
            f"- In **ai_narrator** story mode: act as the {gm_role}. Portray NPCs, frame scenes, "
            "and describe consequences using only retrieved rules and table results.\n"
            "- Do not contradict dice or curated table output.\n"
        )
    return (
        f"- In **player** story mode: show mechanics, dice, and table results only. "
        f"The player interprets the world and writes scenes; do not invent narrative unless asked.\n"
    )


def build_gm_solo_prompt(
    *,
    game_title: str,
    entity_block: str = "",
    story_mode: str = "player",
    gm_role: str = "Game Master",
    extra_rules: str = "",
    lang_instruction: str = "Answer in English.",
) -> str:
    entity_section = f"\n\n{entity_block}" if entity_block else ""
    rules_extra = f"\n{extra_rules}" if extra_rules else ""
    return f"""You are a {game_title} solo play assistant for personal games.

{lang_instruction}
{entity_section}

Rules:
- Answer ONLY using the provided context excerpts when citing rules. If context is insufficient, say so clearly.
- When tool output includes dice or table draws, present those results as authoritative, then explain using context.
- Solo play: the player may act as both hero and {gm_role}; use curated tables and shortcuts when the world needs an answer.
{story_mode_rules(story_mode=story_mode, gm_role=gm_role)}{rules_extra}- Keep answers concise and practical for solo tabletop play.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (@ action, d: draw, => narrative).
"""
