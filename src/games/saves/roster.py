"""Generic multi-slot roster persistence (characters, campaigns, etc.)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable

from src.games.saves.storage import (
    active_slot_path,
    read_json,
    roster_path,
    slot_data_path,
    write_json,
)


@dataclass
class RosterEntry:
    id: str
    name: str
    created_at: str
    updated_at: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class RosterStore:
    """Per-game roster of save slots, each with a JSON entity file."""

    def __init__(
        self,
        game_id: str,
        *,
        entity_filename: str = "entity.json",
        default_slot_name: str = "Slot",
        entity_from_dict: Callable[[dict | None], Any],
        entity_to_dict: Callable[[Any], dict],
        default_entity: Callable[[], Any],
        slot_display_name: Callable[[Any], str],
        before_save: Callable[[Any], None] | None = None,
    ) -> None:
        self.game_id = game_id
        self.entity_filename = entity_filename
        self.default_slot_name = default_slot_name
        self.entity_from_dict = entity_from_dict
        self.entity_to_dict = entity_to_dict
        self.default_entity = default_entity
        self.slot_display_name = slot_display_name
        self.before_save = before_save

    def _entity_path(self, slot_id: str):
        return slot_data_path(self.game_id, slot_id, self.entity_filename)

    def _load_entries(self) -> list[RosterEntry]:
        raw = read_json(roster_path(self.game_id))
        if not isinstance(raw, list):
            return []
        entries: list[RosterEntry] = []
        for row in raw:
            if not isinstance(row, dict) or not row.get("id"):
                continue
            entries.append(
                RosterEntry(
                    id=str(row["id"]),
                    name=str(row.get("name") or self.default_slot_name),
                    created_at=str(row.get("created_at") or _now_iso()),
                    updated_at=str(row.get("updated_at") or _now_iso()),
                )
            )
        return entries

    def _save_entries(self, entries: list[RosterEntry]) -> None:
        write_json(
            roster_path(self.game_id),
            [
                {
                    "id": e.id,
                    "name": e.name,
                    "created_at": e.created_at,
                    "updated_at": e.updated_at,
                }
                for e in entries
            ],
        )

    def list_slots(self) -> list[RosterEntry]:
        return self._load_entries()

    def get_active_slot_id(self) -> str | None:
        raw = read_json(active_slot_path(self.game_id))
        if isinstance(raw, dict) and raw.get("id"):
            return str(raw["id"])
        entries = self._load_entries()
        return entries[0].id if entries else None

    def set_active_slot_id(self, slot_id: str) -> None:
        write_json(active_slot_path(self.game_id), {"id": slot_id})

    def load_entity(self, slot_id: str) -> Any:
        data = read_json(self._entity_path(slot_id))
        entity = self.entity_from_dict(data if isinstance(data, dict) else None)
        if isinstance(entity, dict):
            entity["id"] = slot_id
        elif hasattr(entity, "id"):
            entity.id = slot_id
        return entity

    def save_entity(self, entity: Any) -> None:
        if isinstance(entity, dict):
            slot_id = str(entity.get("id") or "")
        else:
            slot_id = getattr(entity, "id", None) or ""
        if not slot_id:
            raise ValueError("Entity id is required for roster save")
        if self.before_save:
            self.before_save(entity)
        write_json(self._entity_path(slot_id), self.entity_to_dict(entity))
        display = self.slot_display_name(entity)
        entries = self._load_entries()
        now = _now_iso()
        found = False
        for entry in entries:
            if entry.id == slot_id:
                entry.name = display
                entry.updated_at = now
                found = True
                break
        if not found:
            entries.append(
                RosterEntry(id=slot_id, name=display, created_at=now, updated_at=now)
            )
        self._save_entries(entries)

    def create_slot(self, name: str = "") -> Any:
        slot_id = uuid.uuid4().hex[:12]
        entity = self.default_entity()
        if isinstance(entity, dict):
            entity["id"] = slot_id
            if name.strip():
                entity["name"] = name.strip()
        else:
            if hasattr(entity, "id"):
                entity.id = slot_id
            if hasattr(entity, "name") and name.strip():
                entity.name = name.strip()
        self.save_entity(entity)
        self.set_active_slot_id(slot_id)
        return entity

    def delete_slot(self, slot_id: str) -> None:
        import shutil

        entries = [e for e in self._load_entries() if e.id != slot_id]
        self._save_entries(entries)
        slot_path = slot_data_path(self.game_id, slot_id, self.entity_filename).parent
        if slot_path.exists():
            shutil.rmtree(slot_path)
        active = self.get_active_slot_id()
        if active == slot_id:
            if entries:
                self.set_active_slot_id(entries[0].id)
            else:
                path = active_slot_path(self.game_id)
                if path.exists():
                    path.unlink()

    def ensure_initialized(self) -> str:
        entries = self._load_entries()
        if entries:
            active = self.get_active_slot_id()
            if active and any(e.id == active for e in entries):
                return active
            self.set_active_slot_id(entries[0].id)
            return entries[0].id
        entity = self.create_slot()
        return getattr(entity, "id", "")
