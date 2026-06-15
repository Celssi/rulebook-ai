#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.whispers.curated import (
    all_ranks_valid,
    format_card_draw,
    lookup_location,
    lookup_oracle,
    lookup_suit_prompt,
    parse_playing_card,
)

# PDF p.9 — Museum (ace)
assert lookup_location("ace")["title"] == "Museum"
# PDF p.13 — hearts ace blood ring
hearts_ace = lookup_suit_prompt("hearts", "ace")["body"]
assert "blood" in hearts_ace.lower()
# Virtual deck format
assert parse_playing_card("J of hearts")["rank_key"] == "jack"
assert parse_playing_card("Joker (red)")["is_joker"]
# Combined location draw
loc = format_card_draw("A of diamonds", is_location=True)
assert "Museum" in loc["title"] or loc["table"] == "locations"
# Oracle p.47
assert "no" in lookup_oracle(3).lower()
assert "yes" in lookup_oracle(8).lower()
assert all_ranks_valid()
print("validate_whispers_curated: OK")
