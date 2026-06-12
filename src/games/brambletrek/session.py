"""Brambletrek session key helpers."""

from __future__ import annotations

from src.games.saves.keys import session_extra_key, slot_entity_key

GAME_ID = "brambletrek"


def pending_journey_key() -> str:
    return session_extra_key(GAME_ID, "pending_journey")


def character_session_key() -> str:
    return slot_entity_key(GAME_ID)
