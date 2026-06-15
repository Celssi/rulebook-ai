"""Lighthouse roster facade."""

from __future__ import annotations

from src.games.lighthouse.play import get_lighthouse_store
from src.games.saves.roster import RosterEntry


def list_watches() -> list[RosterEntry]:
    return get_lighthouse_store().list_slots()


def load_watch(watch_id: str):
    return get_lighthouse_store().load_entity(watch_id)


def save_watch(watch) -> None:
    get_lighthouse_store().save_entity(watch)


def create_watch(name: str = ""):
    return get_lighthouse_store().create_slot(name)


def delete_watch(watch_id: str) -> None:
    get_lighthouse_store().delete_slot(watch_id)
