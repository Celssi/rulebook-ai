#!/usr/bin/env python3
"""Smoke tests for curated Brambletrek YAML lookups."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.games.brambletrek.character import BrambletrekCharacter
from src.games.brambletrek.actions import match_brambletrek_shortcut
from src.games.brambletrek.curated import (
    adventure_meta,
    adventure_options,
    apply_journey_to_character,
    apply_single_journey_event,
    format_reason_ending,
    journey_depths_trace,
    legacy_abilities,
    legacy_options,
    lookup_journey_event,
    lookup_item,
    lookup_reason_ending,
    lookup_recovery,
    parse_playing_card,
    overcome_the_odds,
    recovery_band,
    apply_item_effects,
    format_item_draw,
)


def main() -> None:
    p = parse_playing_card("9 of spades")
    assert p and p["rank_key"] == "9" and p["suit"] == "spades"

    ev = lookup_journey_event("5 of hearts")
    assert ev and ev.get("morale") == 5 and "depths" in (ev.get("tags") or [])

    assert recovery_band("jack") == "jack-queen"
    rec = lookup_recovery("health", "7 of clubs")
    assert rec and rec.get("band") == "5-7"

    item = lookup_item("7 of hearts")
    assert item and item.get("label") == "Glowing Mushroom"
    assert "Glowing Mushroom" in format_item_draw("7 of hearts")
    char_item = BrambletrekCharacter(health=10, morale=10, supplies=10)
    apply_item_effects(char_item, item)
    assert char_item.health == 11 and char_item.morale == 11

    opts = legacy_options()
    assert "seer" in opts and opts["seer"]["label"] == "Seer"
    st_abs = legacy_abilities("storyteller")
    assert len(st_abs) == 4 and st_abs[0]["id"] == "inspiring_tale"
    assert overcome_the_odds()["id"] == "overcome_the_odds"

    char = BrambletrekCharacter(health=10, morale=10, supplies=10, journey_day=1)
    apply_journey_to_character(char, ["2 of hearts"], increment_day=False)
    assert char.morale == 12

    depths = lookup_journey_event("2 of hearts", in_depths=True)
    assert depths and depths.get("zone") == "aldwund" and depths.get("supplies") == 2

    trace = journey_depths_trace(
        ["2 of hearts", "3 of hearts"], start_in_aldwund=True
    )
    assert trace == [True, True]
    apply_single_journey_event(char, "5 of hearts", in_depths=True)
    assert char.morale == 17 and not char.in_aldwund  # depths hearts 5: +5 morale, (EXIT)

    assert lookup_reason_ending("jack")["title"] == "Lost Light"
    assert "fireflies" in format_reason_ending("jack").lower()

    from src.games.brambletrek.curated import (
        format_combat_setup_curated,
        lookup_opponent_tactic,
        lookup_player_tactic,
    )

    assert lookup_opponent_tactic("7 of spades")["label"].startswith("Terrifying")
    assert lookup_player_tactic("seer", "5 of hearts")["effect"].startswith("Healing")
    setup = format_combat_setup_curated(
        ["8 of hearts", "3 of clubs", "5 of diamonds", "9 of spades", "jack of hearts", "2 of clubs"],
        legacy_id="seer",
        legacy_label="Seer",
    )
    assert "Opponent Tactics" in setup
    assert "Tactic 1" in setup
    assert "goes first" in setup

    assert adventure_options()
    assert adventure_meta("pumpkin_party")["pdf_page_min"] == 85
    assert adventure_meta("birthday_wonders")["faction"] == "adventure"
    assert "Complete Digital" in adventure_meta("first_frost")["source_label"]

    assert match_brambletrek_shortcut("today's journey cards", active_adventure="") == "journey_day"
    assert (
        match_brambletrek_shortcut("today's journey cards", active_adventure="pumpkin_party")
        == "adventure_scene"
    )
    assert (
        match_brambletrek_shortcut(
            "journey and exploration page 24", active_adventure="pumpkin_party"
        )
        == "journey_day"
    )

    print("validate_brambletrek_curated: OK")


if __name__ == "__main__":
    main()
