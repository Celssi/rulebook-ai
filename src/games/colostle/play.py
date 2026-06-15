"""Colostle play roster registration."""

from __future__ import annotations

from src.games.colostle.character import (
    ColostleCharacter,
    character_from_dict,
    character_to_dict,
    default_character,
)
from src.games.saves import PlayProfile, get_play_store, register_play_profile

GAME_ID = "colostle"


def _slot_name(entity: ColostleCharacter) -> str:
    return entity.name.strip()


def _lonelog_name(entity: ColostleCharacter) -> str:
    return entity.name.strip() or "Adventurer"


def _resolve_modes(ctx):
    from src.games.colostle import play_handlers as ph

    card_source, story_mode, _ = ph.get_play_settings(ctx)
    return story_mode, card_source


def _entity_for_rag(ctx):
    from src.games.colostle import play_handlers as ph

    return character_to_dict(ph.get_character(ctx))


def _register() -> None:
    from src.games.colostle import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.colostle.agent import colostle_multi_node

        return colostle_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="Colostle",
            slot_label="Adventurer",
            default_slot_name="",
            entity_filename="character.json",
            entity_from_dict=character_from_dict,
            entity_to_dict=character_to_dict,
            default_entity=default_character,
            slot_display_name=_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda c: c.clamp(),
            has_lonelog=True,
            play_settings={
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
                "location_mode": {
                    "default": "roomlands",
                    "choices": ["roomlands", "ocean", "city", "battlements"],
                },
            },
            session_extra_keys=[],
            resolve_play_modes=_resolve_modes,
            try_handle_prompt=ph.try_handle_prompt,
            entity_for_rag=_entity_for_rag,
            agent_multi_node=_agent_node,
        )
    )


def get_colostle_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Colostle play profile not registered")
    return store


