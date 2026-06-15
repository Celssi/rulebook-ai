"""Coriolis: The Great Dark system prompt builder."""

from __future__ import annotations

from src.games.coriolis.character import CoriolisExplorer, format_for_prompt
from src.games.gm_solo.prompts import build_gm_solo_prompt


def coriolis_system_prompt(
    *,
    character: CoriolisExplorer | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
    language_instruction: str = "Answer in English.",
) -> str:
    entity_block = format_for_prompt(character, story_mode=story_mode, card_source=card_source)
    extra = (
        "- Coriolis: The Great Dark uses attribute + talent base dice and optional gear dice; "
        "sixes are successes.\n"
        "- Pushing rerolls non-six/non-one dice; base ones cost Hope, gear ones reduce gear bonus.\n"
        "- Track Health, Hope, and Heart; despair and Blight from the rulebook.\n"
    )
    return build_gm_solo_prompt(
        game_title="Coriolis — The Great Dark",
        entity_block=entity_block,
        story_mode=story_mode,
        gm_role="Game Master",
        extra_rules=extra,
        lang_instruction=language_instruction,
    )
