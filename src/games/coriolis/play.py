"""Coriolis play roster registration."""

from __future__ import annotations

from src.games.coriolis.actions import SHORTCUT_IDS
from src.games.coriolis.character import (
    CoriolisCrew,
    crew_from_dict,
    crew_to_dict,
    default_crew,
)
from src.games.coriolis.play_handlers import HANDLERS
from src.games.gm_solo.play_factory import register_gm_play
from src.games.saves import get_play_store

GAME_ID = "coriolis"


def _slot_name(entity: CoriolisCrew) -> str:
    return entity.name.strip() or entity.crew_name.strip()


def _lonelog_name(entity: CoriolisCrew) -> str:
    return entity.name.strip() or entity.crew_name.strip() or "Crew"


register_gm_play(
    game_id=GAME_ID,
    game_label="Coriolis",
    slot_label="Crew member",
    default_slot_name="",
    entity_filename="crew.json",
    entity_from_dict=crew_from_dict,
    entity_to_dict=crew_to_dict,
    default_entity=default_crew,
    slot_display_name=_slot_name,
    lonelog_display_name=_lonelog_name,
    handlers=HANDLERS,
    shortcut_ids=SHORTCUT_IDS,
    before_save_entity=lambda c: c.clamp(),
)


def get_coriolis_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Coriolis play profile not registered")
    return store
