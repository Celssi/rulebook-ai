"""Brambletrek 2 roster facade."""

from __future__ import annotations

from src.games.brambletrek_2.play import get_brambletrek_2_store
from src.games.saves.roster import RosterEntry


def list_characters() -> list[RosterEntry]:
    return get_brambletrek_2_store().list_slots()


def load_character(char_id: str):
    return get_brambletrek_2_store().load_entity(char_id)


def save_character(char) -> None:
    get_brambletrek_2_store().save_entity(char)


def create_character(name: str = ""):
    return get_brambletrek_2_store().create_slot(name)


def delete_character(char_id: str) -> None:
    get_brambletrek_2_store().delete_slot(char_id)
