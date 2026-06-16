"""Brambletrek play roster registration (uses generic src.games.saves)."""

from __future__ import annotations

from src.games.brambletrek.character import (
    BrambletrekCharacter,
    character_from_dict,
    character_to_dict,
    default_character,
)
from src.games.saves import PlayProfile, get_play_store, register_play_profile

GAME_ID = "brambletrek"


def _roster_slot_name(entity: BrambletrekCharacter) -> str:
    return entity.name.strip()


def _lonelog_name(entity: BrambletrekCharacter) -> str:
    return entity.name.strip() or "Gnawborn"


def _register() -> None:
    from src.games.brambletrek import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.brambletrek.agent import brambletrek_multi_node

        return brambletrek_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="Brambletrek",
            slot_label="Gnawborn",
            default_slot_name="",
            entity_filename="character.json",
            entity_from_dict=character_from_dict,
            entity_to_dict=character_to_dict,
            default_entity=default_character,
            slot_display_name=_roster_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda c: c.clamp_stats(),
            has_lonelog=True,
            play_settings={
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
            },
            session_extra_keys=["pending_journey", "resource_draft"],
            resolve_play_modes=ph.get_play_settings,
            log_user_prompt=ph.log_user_prompt,
            try_handle_prompt=ph.try_handle_prompt,
            entity_for_rag=lambda ctx: ctx.entity,
            agent_multi_node=_agent_node,
        )
    )


def get_brambletrek_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Brambletrek play profile not registered")
    return store


