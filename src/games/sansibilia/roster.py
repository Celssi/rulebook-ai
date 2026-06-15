"""San Sibilia roster — thin facade over generic PlayStore."""

from __future__ import annotations

from src.games.sansibilia.play import get_sansibilia_store
from src.games.saves.roster import RosterEntry
from src.games.saves.storage import game_saves_dir

SAVES_DIR = game_saves_dir("sansibilia")


def list_visits() -> list[RosterEntry]:
    return get_sansibilia_store().list_slots()


def get_active_visit_id() -> str | None:
    return get_sansibilia_store().roster.get_active_slot_id()


def load_visit(visit_id: str):
    return get_sansibilia_store().load_entity(visit_id)


def save_visit(visit) -> None:
    get_sansibilia_store().save_entity(visit)


def create_visit(name: str = ""):
    return get_sansibilia_store().create_slot(name)


def delete_visit(visit_id: str) -> None:
    get_sansibilia_store().delete_slot(visit_id)


def rename_visit(visit_id: str, name: str) -> None:
    visit = load_visit(visit_id)
    if hasattr(visit, "name"):
        visit.name = name.strip()
    elif isinstance(visit, dict):
        visit["name"] = name.strip()
    save_visit(visit)


def ensure_roster_initialized() -> str:
    return get_sansibilia_store().ensure_initialized()
