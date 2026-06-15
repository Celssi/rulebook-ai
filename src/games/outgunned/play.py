"""Outgunned play roster registration."""

from __future__ import annotations

from src.games.gm_solo.play_factory import register_gm_play
from src.games.outgunned.actions import SHORTCUT_IDS
from src.games.outgunned.character import (
    OutgunnedHero,
    default_hero,
    format_for_prompt,
    hero_from_dict,
    hero_to_dict,
)
from src.games.outgunned.play_handlers import HANDLERS
from src.games.saves import get_play_store

GAME_ID = "outgunned"


def _slot_name(entity: OutgunnedHero) -> str:
    return entity.name.strip()


def _lonelog_name(entity: OutgunnedHero) -> str:
    return entity.name.strip() or "Hero"


register_gm_play(
    game_id=GAME_ID,
    game_label="Outgunned",
    slot_label="Hero",
    default_slot_name="",
    entity_filename="hero.json",
    entity_from_dict=hero_from_dict,
    entity_to_dict=hero_to_dict,
    default_entity=default_hero,
    slot_display_name=_slot_name,
    lonelog_display_name=_lonelog_name,
    handlers=HANDLERS,
    shortcut_ids=SHORTCUT_IDS,
    before_save_entity=lambda h: h.clamp(),
)


def get_outgunned_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Outgunned play profile not registered")
    return store
