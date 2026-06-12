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


def _display_name(entity: BrambletrekCharacter) -> str:
    return entity.name.strip() or "Gnawborn"


BRAMBLETREK_PROFILE = PlayProfile(
    game_id=GAME_ID,
    game_label="Brambletrek",
    slot_label="Gnawborn",
    default_slot_name="Gnawborn",
    entity_filename="character.json",
    entity_from_dict=character_from_dict,
    entity_to_dict=character_to_dict,
    default_entity=default_character,
    slot_display_name=_display_name,
    lonelog_display_name=_display_name,
    before_save_entity=lambda c: c.clamp_stats(),
    has_lonelog=True,
    play_settings={
        "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
        "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
    },
    session_extra_keys=["pending_journey"],
)

register_play_profile(BRAMBLETREK_PROFILE)


def get_brambletrek_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Brambletrek play profile not registered")
    return store
