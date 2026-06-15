"""Outgunned system prompt builder."""

from __future__ import annotations

from src.games.gm_solo.prompts import build_gm_solo_prompt
from src.games.outgunned.character import OutgunnedHero, format_for_prompt


def outgunned_system_prompt(
    *,
    character: OutgunnedHero | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
    language_instruction: str = "Answer in English.",
) -> str:
    entity_block = format_for_prompt(character, story_mode=story_mode, card_source=card_source)
    extra = (
        "- Outgunned Adventure uses d6 pools where successes come from **matching pairs** "
        "(Basic 2-of-a-kind, Critical 3, Extreme 4, etc.) and the **Assistant Director** "
        "for solo play prompts.\n"
        "- Missions have phases; use AD draws when you need scene direction without a human Director.\n"
    )
    return build_gm_solo_prompt(
        game_title="Outgunned Adventure",
        entity_block=entity_block,
        story_mode=story_mode,
        gm_role="Director",
        extra_rules=extra,
        lang_instruction=language_instruction,
    )
