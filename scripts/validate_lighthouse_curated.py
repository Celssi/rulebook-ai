#!/usr/bin/env python3
"""Smoke-test Lighthouse curated YAML tables."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.games.lighthouse.curated import (
    all_beachcombing_ranks_valid,
    all_event_ranks_valid,
    beachcombing_card_count,
    format_event,
    format_light_lamp,
    format_maintenance,
    format_observation,
    lookup_weather,
    parse_playing_card,
    weather_options,
)


def main() -> int:
    assert all_event_ranks_valid()
    assert all_beachcombing_ranks_valid()
    assert len(weather_options()) == 8
    assert lookup_weather("anxious")["label"] == "Anxious"

    assert parse_playing_card("J of hearts")["rank_key"] == "jack"
    assert parse_playing_card("7 of clubs")["color"] == "black"

    lamp = format_light_lamp("3 of hearts", {"heads": True, "side": "heads"})
    assert lamp["lit"] is True
    lamp_fail = format_light_lamp("3 of clubs", {"heads": True, "side": "heads"})
    assert lamp_fail["lit"] is False

    maint = format_maintenance(3, "5 of spades")
    assert "tending" in maint["task"].lower()
    assert maint["outcome"]

    obs = format_observation(2, "Q of diamonds")
    assert "vessels" in obs["subject"].lower()
    assert obs["distance"]

    ev = format_event("9 of hearts")
    assert ev["event"]
    assert ev["color"] == "red"

    assert beachcombing_card_count(14) == 7
    assert beachcombing_card_count(15) == 8

    print("validate_lighthouse_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
