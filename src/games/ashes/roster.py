"""Ashes roster facade."""

from __future__ import annotations

from src.games.ashes.play import get_ashes_store
from src.games.saves.roster import RosterEntry


def list_scions() -> list[RosterEntry]:
    return get_ashes_store().list_slots()


def load_scion(scion_id: str):
    return get_ashes_store().load_entity(scion_id)


def save_scion(scion) -> None:
    get_ashes_store().save_entity(scion)


def create_scion(name: str = ""):
    return get_ashes_store().create_slot(name)


def delete_scion(scion_id: str) -> None:
    get_ashes_store().delete_slot(scion_id)
