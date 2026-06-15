#!/usr/bin/env python3
"""Validate Brambletrek 2 roster + lonelog."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.games.brambletrek_2.character import default_character  # noqa: E402
from src.games.brambletrek_2.lonelog import format_resources, format_scene_header  # noqa: E402
from src.games.brambletrek_2.play import GAME_ID, get_brambletrek_2_store  # noqa: E402
from src.games.saves import get_play_store  # noqa: E402


def main() -> int:
    assert get_play_store(GAME_ID) is not None
    store = get_brambletrek_2_store()
    assert store.game_id == "brambletrek_2"
    char = default_character()
    char.name = "Test Traveller"
    char.legacy = "pooh"
    char.health = 12
    char.morale = 14
    char.supplies = 10
    char.exploration_day = 1
    snap = format_resources(char.health, char.morale, char.supplies, name=char.name)
    assert "Health 12" in snap
    header = format_scene_header(char)
    assert "Hundred Acre" in header
    char.in_hollow = True
    char.memory_fragments = 2
    assert "Misty Hollow" in format_scene_header(char)
    print("validate_brambletrek_2_lonelog: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
