"""MLP play roster registration."""

from __future__ import annotations

from src.games.gm_solo.play_factory import register_gm_play
from src.games.mlp.entity import MlpPony, default_pony, pony_from_dict, pony_to_dict
from src.games.mlp.play_handlers import HANDLERS
from src.games.saves import get_play_store

GAME_ID = "mlp"


def _slot_name(entity: MlpPony) -> str:
    return (entity.pony_name or entity.name).strip()


def _lonelog_name(entity: MlpPony) -> str:
    return (entity.pony_name or entity.name).strip() or "Pony"


register_gm_play(
    game_id=GAME_ID,
    game_label="My Little Pony RPG",
    slot_label="Pony",
    default_slot_name="",
    entity_filename="character.json",
    entity_from_dict=pony_from_dict,
    entity_to_dict=pony_to_dict,
    default_entity=default_pony,
    slot_display_name=_slot_name,
    lonelog_display_name=_lonelog_name,
    handlers=HANDLERS,
    shortcut_ids=HANDLERS.shortcut_ids,
    before_save_entity=lambda p: p.clamp(),
)


def get_mlp_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("MLP play profile not registered")
    return store
