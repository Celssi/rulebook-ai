"""Streamlit session_state key naming for play rosters (per game_id)."""


def active_slot_key(game_id: str) -> str:
    return f"{game_id}_active_slot_id"


def slot_entity_key(game_id: str) -> str:
    """Session key for the active slot's entity dict (e.g. character sheet)."""
    return f"{game_id}_slot_entity"


def play_setting_key(game_id: str, setting: str) -> str:
    return f"{game_id}_{setting}"


def session_extra_key(game_id: str, extra: str) -> str:
    return f"{game_id}_extra_{extra}"
