"""Brambletrek roster — thin facade over generic PlayStore."""

from __future__ import annotations

from src.games.brambletrek.play import get_brambletrek_store
from src.games.saves.roster import RosterEntry
from src.games.saves.storage import game_saves_dir

SAVES_DIR = game_saves_dir("brambletrek")


def list_characters() -> list[RosterEntry]:
    return get_brambletrek_store().list_slots()


def get_active_character_id() -> str | None:
    return get_brambletrek_store().roster.get_active_slot_id()


def load_character(char_id: str):
    return get_brambletrek_store().load_entity(char_id)


def save_character(char) -> None:
    get_brambletrek_store().save_entity(char)


def create_character(name: str = ""):
    return get_brambletrek_store().create_slot(name)


def delete_character(char_id: str) -> None:
    get_brambletrek_store().delete_slot(char_id)


def ensure_roster_initialized() -> str:
    return get_brambletrek_store().ensure_initialized()
