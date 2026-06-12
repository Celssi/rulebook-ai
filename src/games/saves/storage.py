"""Filesystem layout and JSON helpers for per-game save slots."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.settings import DATA_DIR

SAVES_ROOT = DATA_DIR / "saves"


def game_saves_dir(game_id: str) -> Path:
    return SAVES_ROOT / game_id


def slot_dir(game_id: str, slot_id: str) -> Path:
    return game_saves_dir(game_id) / slot_id


def roster_path(game_id: str) -> Path:
    return game_saves_dir(game_id) / "roster.json"


def active_slot_path(game_id: str) -> Path:
    return game_saves_dir(game_id) / "active.json"


def slot_data_path(game_id: str, slot_id: str, filename: str) -> Path:
    return slot_dir(game_id, slot_id) / filename


def read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return None


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
