"""The One Ring system prompt builder."""

from __future__ import annotations

from src.games.gm_solo.prompts import build_gm_solo_prompt
from src.games.tor.entity import TorHero, format_for_prompt


def tor_system_prompt(
    *,
    character: TorHero | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
    language_instruction: str = "Answer in English.",
) -> str:
    entity_block = format_for_prompt(character, story_mode=story_mode, card_source=card_source)
    extra = (
        "- Strider Mode solo play uses the Telling Table (yes/no), Lore Table (Action/Aspect/Focus), "
        "Fortune and Ill-Fortune tables, patron quests, and solo journey events.\n"
        "- Skill rolls use a Feat d12 and Success dice; Gandalf rune and Eye of Sauron are special results.\n"
        "- Track Hope, Dread (Shadow), Weary, Eye Awareness, patron, safe haven, and journey day on the hero sheet.\n"
    )
    return build_gm_solo_prompt(
        game_title="The One Ring (Strider Mode)",
        entity_block=entity_block,
        story_mode=story_mode,
        gm_role="Loremaster",
        extra_rules=extra,
        lang_instruction=language_instruction,
    )
