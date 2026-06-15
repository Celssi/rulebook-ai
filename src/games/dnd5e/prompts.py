"""D&D 5e system prompt builder."""

from __future__ import annotations

from src.games.dnd5e.entity import Dnd5eCharacter, format_for_prompt
from src.games.gm_solo.prompts import build_gm_solo_prompt


def dnd5e_system_prompt(
    *,
    character: Dnd5eCharacter | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
    language_instruction: str = "Answer in English.",
) -> str:
    entity_block = format_for_prompt(character, story_mode=story_mode, card_source=card_source)
    extra = (
        "- D&D 5e uses d20 tests with advantage/disadvantage for ability checks, saves, and attacks.\n"
        "- Track HP, AC, ability scores, spell slots, and level on the character sheet.\n"
        "- Solo play: use the d6 yes/no oracle when you need an impartial answer; rests follow PHB rules.\n"
    )
    if character:
        setting = (character.campaign_setting or "freeform").strip().lower()
        notes = (character.campaign_notes or "").strip()
        if setting == "faerun":
            extra += (
                "- Campaign setting: Faerûn (Forgotten Realms). "
                "Use Heroes of Faerûn and Adventures in Faerûn when relevant.\n"
            )
        elif notes:
            extra += f"- Campaign setting (player-defined): {notes}\n"
        else:
            extra += (
                "- Campaign setting: freeform/homebrew. Do not assume Faerûn unless the player asks.\n"
            )
    return build_gm_solo_prompt(
        game_title="D&D 5e solo",
        entity_block=entity_block,
        story_mode=story_mode,
        gm_role="Dungeon Master",
        extra_rules=extra,
        lang_instruction=language_instruction,
    )
