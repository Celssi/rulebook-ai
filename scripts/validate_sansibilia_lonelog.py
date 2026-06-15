#!/usr/bin/env python3
"""Smoke-test San Sibilia Lonelog formatters."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.games.sansibilia.lonelog import (
    format_city_change_note,
    format_day_draw_line,
    format_day_header,
    narrative_context_for_ai,
)
from src.games.sansibilia.visit import SansibiliaVisit, visit_from_dict, visit_to_dict


def main() -> int:
    visit = SansibiliaVisit(name="Traveler", visit_day=3, archetype="curious scholar")
    header = format_day_header(visit)
    assert "Day 3" in header
    assert "San Sibilia" in header

    note = format_city_change_note("Two Hearts in a Row", "A change of heart.")
    assert "City change" in note

    draw_line = format_day_draw_line(
        visit,
        "6 of spades",
        "5 of hearts",
        "intriguing",
        "poetry reading",
    )
    assert draw_line.startswith("d: Day 3 intriguing · poetry reading 2 ->")
    assert "6♠" in draw_line or "6" in draw_line

    roundtrip = visit_from_dict(visit_to_dict(visit))
    assert roundtrip.name == "Traveler"
    assert roundtrip.visit_day == 3

    from src.games.sansibilia import lonelog as sl

    class _FakeStore:
        def read_log_tail(self, _slot_id: str, n_lines: int = 50) -> list[str]:
            _ = n_lines
            return [
                "d: Day 1 foo · bar 2 -> 3♠, 4♥",
                "=> First evening at the river.",
                "S2 *San Sibilia, Day 2*",
                "=> Market trouble with the guild.",
            ]

    orig = sl.get_sansibilia_store
    sl.get_sansibilia_store = lambda: _FakeStore()  # type: ignore[assignment]
    try:
        ctx = sl.narrative_context_for_ai("test")
        assert "First evening at the river" in ctx
        assert "Market trouble" in ctx
        assert "Day 2" in ctx
        assert "d: Day 1" not in ctx
    finally:
        sl.get_sansibilia_store = orig

    print("validate_sansibilia_lonelog: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
