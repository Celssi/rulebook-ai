"""Brambletrek session helpers — thin facade over generic PlayStore."""

from __future__ import annotations

from src.games.brambletrek.play import get_brambletrek_store
from src.games.saves.keys import session_extra_key, slot_entity_key

GAME_ID = "brambletrek"


def get_play_settings(st) -> tuple[str, str]:
    settings = get_brambletrek_store().get_settings(st)
    return settings.get("story_mode", "player"), settings.get("card_source", "virtual")


def active_char_id(st) -> str:
    return get_brambletrek_store().active_slot_id(st)


def persist_current_session(st) -> None:
    get_brambletrek_store().persist(st)


def switch_character(st, new_char_id: str) -> None:
    get_brambletrek_store().switch_slot(st, new_char_id)


def init_brambletrek_session(st) -> None:
    get_brambletrek_store().init_streamlit(st)


def pending_journey_key() -> str:
    return session_extra_key(GAME_ID, "pending_journey")


def character_session_key() -> str:
    return slot_entity_key(GAME_ID)
