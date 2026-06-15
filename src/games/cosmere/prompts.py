"""Cosmere system prompt builder."""

from __future__ import annotations

from src.games.cosmere.entity import CosmereCharacter, format_for_prompt
from src.games.gm_solo.prompts import build_gm_solo_prompt


def cosmere_system_prompt(
    *,
    character: CosmereCharacter | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
    language_instruction: str = "Answer in English.",
) -> str:
    entity_block = format_for_prompt(character, story_mode=story_mode, card_source=card_source)
    extra = (
        "- Cosmere RPG uses plot dice (d6): **1** = complication, **6** = opportunity.\n"
        "- Skill tests use d20 with advantage/disadvantage; paths, roles, and expertises shape fiction.\n"
        "- Combat uses attack rolls against deflection; spend plot dice for extra effects.\n"
    )
    return build_gm_solo_prompt(
        game_title="Cosmere RPG (Stormlight)",
        entity_block=entity_block,
        story_mode=story_mode,
        gm_role="Game Master",
        extra_rules=extra,
        lang_instruction=language_instruction,
    )
