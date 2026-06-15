"""MLP system prompt builder."""

from __future__ import annotations

from src.games.gm_solo.prompts import build_gm_solo_prompt
from src.games.mlp.entity import MlpPony, format_for_prompt


def mlp_system_prompt(
    *,
    pony: MlpPony | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
    language_instruction: str = "Answer in English.",
) -> str:
    entity_block = format_for_prompt(pony, story_mode=story_mode, card_source=card_source)
    extra = (
        "- MLP RPG uses Essence20 Skill Tests: d20 + skill die vs Difficulty (DIF).\n"
        "- Edge/Snag: roll 2d20 and take best/worst on the d20 only.\n"
        "- Spellcasting uses the Magic Shift tracking ladder; spells cost downshifts, recover +1 per turn.\n"
        "- Friendship Points are a shared pool; players spend them for rerolls, temp Specialization, +5 Defense, or GM hints.\n"
        "- Encounters in Ponyville provides ready scene hooks when using the encounter shortcut.\n"
    )
    return build_gm_solo_prompt(
        game_title="My Little Pony RPG",
        entity_block=entity_block,
        story_mode=story_mode,
        gm_role="Game Master",
        extra_rules=extra,
        lang_instruction=language_instruction,
    )
