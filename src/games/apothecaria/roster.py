"""Apothecaria cottage roster."""

from __future__ import annotations

from src.games.apothecaria.cottage import WitchCottage, cottage_from_dict, cottage_to_dict
from src.games.apothecaria.play import get_apothecaria_store
from src.games.saves import game_saves_dir

SAVES_DIR = game_saves_dir("apothecaria")


def list_cottages():
    return get_apothecaria_store().list_slots()


def active_cottage_id() -> str | None:
    return get_apothecaria_store().roster.get_active_slot_id()


def load_cottage(cottage_id: str) -> WitchCottage:
    return get_apothecaria_store().load_entity(cottage_id)


def save_cottage(cottage: WitchCottage) -> None:
    get_apothecaria_store().save_entity(cottage)


def create_cottage(name: str) -> WitchCottage:
    return get_apothecaria_store().create_slot(name)


def delete_cottage(cottage_id: str) -> None:
    get_apothecaria_store().delete_slot(cottage_id)


def ensure_initialized():
    return get_apothecaria_store().ensure_initialized()
