"""Colostle roster facade."""

from __future__ import annotations

from src.games.colostle.character import character_from_dict
from src.games.colostle.play import get_colostle_store
from src.games.saves.roster import RosterEntry


def list_characters() -> list[RosterEntry]:
    return get_colostle_store().list_slots()


def load_character(char_id: str):
    return character_from_dict(get_colostle_store().load_entity(char_id))


def save_character(char) -> None:
    get_colostle_store().save_entity(char)


def create_character(name: str = ""):
    return get_colostle_store().create_slot(name)


def delete_character(char_id: str) -> None:
    get_colostle_store().delete_slot(char_id)
