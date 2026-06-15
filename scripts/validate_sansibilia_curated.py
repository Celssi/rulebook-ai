#!/usr/bin/env python3
"""Smoke-test San Sibilia curated YAML tables."""

from __future__ import annotations

import sys

from src.games.sansibilia.curated import (
    all_ranks_valid,
    detect_city_change,
    format_character_archetype,
    format_character_draw,
    format_day_draw,
    lookup_adjective,
    lookup_character_role,
    lookup_character_trait,
    lookup_location_event,
    parse_playing_card,
)


def main() -> int:
    assert all_ranks_valid(), "missing rank entries in curated tables"
    assert lookup_character_trait("ace") == "failed"
    assert lookup_character_role("king") == "critic"
    assert format_character_archetype("lonely", "journalist") == "Lonely journalist"

    card1, card2 = "4 of spades", "Queen of diamonds"
    day = format_day_draw(card1, card2)
    assert day["adjective"] == lookup_adjective(card1)
    assert day["location_event"] == lookup_location_event(card2)
    assert day["prompt"]

    same_suit = detect_city_change("7 of hearts", "Jack of hearts")
    assert same_suit and same_suit["kind"] == "same_suit"

    same_val = detect_city_change("5 of clubs", "5 of diamonds")
    assert same_val and same_val["kind"] == "same_value"

    char = format_character_draw(["2 of clubs", "King of spades"])
    assert char["trait"] == "lonely"
    assert char["role"] == "critic"
    assert char["archetype"] == "Lonely critic"

    parsed = parse_playing_card("Ace of clubs")
    assert parsed and parsed["rank_key"] == "ace"

    # Virtual deck uses single-letter face ranks (J/Q/K/A)
    assert parse_playing_card("J of hearts") and parse_playing_card("J of hearts")["rank_key"] == "jack"
    j_day = format_day_draw("7 of clubs", "J of hearts")
    assert j_day["adjective"] == "harrowing"
    assert j_day["location_event"] == "funeral procession at dawn"

    # PDF p.10 sample: 4♠ → intriguing, Q♦ → find in the antique store
    assert lookup_adjective("4 of spades") == "intriguing"
    assert lookup_location_event("Queen of diamonds") == "find in the antique store"
    sample = format_day_draw("4 of spades", "Queen of diamonds")
    assert sample["prompt"] == "intriguing find in the antique store"

    # PDF p.8–9 spot checks (red vs black by suit color)
    assert lookup_adjective("Ace of hearts") == "serendipitous"
    assert lookup_adjective("Ace of clubs") == "illicit"
    assert lookup_location_event("5 of diamonds") == "coffee in an open air cafe"
    assert lookup_location_event("5 of clubs") == "walk in the park"

    # PDF p.12 city-change titles
    hearts = detect_city_change("2 of hearts", "9 of hearts")
    assert hearts and hearts["title"] == "Two Hearts in a Row"
    same_val = detect_city_change("10 of spades", "10 of diamonds")
    assert same_val and same_val["title"] == "Two of the Same Value in a Row"

    print("validate_sansibilia_curated: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
