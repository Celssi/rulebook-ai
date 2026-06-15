"""D&D 5e play roster registration."""

from __future__ import annotations

from src.games.dnd5e.entity import Dnd5eCharacter, character_from_dict, character_to_dict, default_character
from src.games.dnd5e.play_handlers import HANDLERS
from src.games.gm_solo.play_factory import register_gm_play
from src.games.saves import get_play_store

GAME_ID = "dnd5e"


def _slot_name(entity: Dnd5eCharacter) -> str:
    return entity.name.strip()


def _lonelog_name(entity: Dnd5eCharacter) -> str:
    return entity.name.strip() or "Character"


register_gm_play(
    game_id=GAME_ID,
    game_label="D&D 5e solo",
    slot_label="Character",
    default_slot_name="",
    entity_filename="character.json",
    entity_from_dict=character_from_dict,
    entity_to_dict=character_to_dict,
    default_entity=default_character,
    slot_display_name=_slot_name,
    lonelog_display_name=_lonelog_name,
    handlers=HANDLERS,
    shortcut_ids=HANDLERS.shortcut_ids,
    before_save_entity=lambda c: c.clamp(),
)


def get_dnd5e_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("D&D 5e play profile not registered")
    return store
