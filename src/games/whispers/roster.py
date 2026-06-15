"""Whispers roster — thin facade over generic PlayStore."""

from __future__ import annotations

from src.games.saves.roster import RosterEntry
from src.games.saves.storage import game_saves_dir
from src.games.whispers.play import get_whispers_store

SAVES_DIR = game_saves_dir("whispers")


def list_investigations() -> list[RosterEntry]:
    return get_whispers_store().list_slots()


def get_active_investigation_id() -> str | None:
    return get_whispers_store().roster.get_active_slot_id()


def load_investigation(investigation_id: str):
    return get_whispers_store().load_entity(investigation_id)


def save_investigation(inv) -> None:
    get_whispers_store().save_entity(inv)


def create_investigation(name: str = ""):
    return get_whispers_store().create_slot(name)


def delete_investigation(investigation_id: str) -> None:
    get_whispers_store().delete_slot(investigation_id)
