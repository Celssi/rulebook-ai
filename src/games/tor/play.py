"""The One Ring play roster registration."""

from __future__ import annotations

from src.games.gm_solo.play_factory import register_gm_play
from src.games.saves import get_play_store
from src.games.tor.entity import TorHero, hero_from_dict, hero_to_dict, default_hero
from src.games.tor.play_handlers import HANDLERS

GAME_ID = "tor"


def _slot_name(entity: TorHero) -> str:
    return entity.name.strip()


def _lonelog_name(entity: TorHero) -> str:
    return entity.name.strip() or "Hero"


register_gm_play(
    game_id=GAME_ID,
    game_label="The One Ring (Strider Mode)",
    slot_label="Hero",
    default_slot_name="",
    entity_filename="hero.json",
    entity_from_dict=hero_from_dict,
    entity_to_dict=hero_to_dict,
    default_entity=default_hero,
    slot_display_name=_slot_name,
    lonelog_display_name=_lonelog_name,
    handlers=HANDLERS,
    shortcut_ids=HANDLERS.shortcut_ids,
    before_save_entity=lambda h: h.clamp(),
)


def get_tor_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("TOR play profile not registered")
    return store
