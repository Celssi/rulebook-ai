"""Dispatch system prompts for GM solo games."""

from __future__ import annotations

from src.games.registry import GM_SOLO_GAME_IDS


def gm_solo_system_prompt(
    game_id: str,
    *,
    play_entity: dict | None,
    story_mode: str,
    card_source: str,
    language_instruction: str = "Answer in English.",
) -> str | None:
    if game_id not in GM_SOLO_GAME_IDS:
        return None

    if game_id == "tor":
        from src.games.tor.entity import hero_from_dict
        from src.games.tor.prompts import tor_system_prompt

        return tor_system_prompt(
            character=hero_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
            language_instruction=language_instruction,
        )

    if game_id == "dnd5e":
        from src.games.dnd5e.entity import character_from_dict
        from src.games.dnd5e.prompts import dnd5e_system_prompt

        return dnd5e_system_prompt(
            character=character_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
            language_instruction=language_instruction,
        )

    if game_id == "cosmere":
        from src.games.cosmere.entity import character_from_dict
        from src.games.cosmere.prompts import cosmere_system_prompt

        return cosmere_system_prompt(
            character=character_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
            language_instruction=language_instruction,
        )

    if game_id == "mlp":
        from src.games.mlp.entity import pony_from_dict
        from src.games.mlp.prompts import mlp_system_prompt

        return mlp_system_prompt(
            pony=pony_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
            language_instruction=language_instruction,
        )

    if game_id == "outgunned":
        from src.games.outgunned.character import character_from_dict
        from src.games.outgunned.prompts import outgunned_system_prompt

        return outgunned_system_prompt(
            character=character_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
            language_instruction=language_instruction,
        )

    if game_id == "coriolis":
        from src.games.coriolis.character import crew_from_dict
        from src.games.coriolis.prompts import coriolis_system_prompt

        return coriolis_system_prompt(
            character=crew_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
            language_instruction=language_instruction,
        )

    return None
