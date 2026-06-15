#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.colostle.curated import (
    all_ranks_valid,
    all_roomlands_ranks_valid,
    format_character_draw,
    format_exploration_draw,
    format_person_opponent,
    format_rook_opponent,
    lookup_item,
    lookup_oracle,
    lookup_roomlands,
    parse_playing_card,
)

def main() -> int:
    assert all_ranks_valid()
    assert all_roomlands_ranks_valid()
    # PDF rules-reference p.1 — ace hearts roomlands red
    assert parse_playing_card("J of hearts")["rank_key"] == "jack"
    red = lookup_roomlands("4 of diamonds")
    assert "PERSON NEEDS YOU" in red["prompt"]
    black = lookup_roomlands("3 of spades")
    assert "STAIRCASE" in black["prompt"]
    face = lookup_roomlands("Q of hearts")
    assert "Medium Rook" in face["prompt"]
    assert lookup_item("jack") == "WEAPON"
    oracle = lookup_oracle("7 of clubs")
    assert oracle["answer"] == "Yes"
    sample = format_exploration_draw(["J of hearts", "4 of spades"])
    assert len(sample) == 2
    char = format_character_draw("Ace of hearts", "King of clubs")
    assert char["calling"]
    assert char["nature"]
    person = format_person_opponent("2 of spades", "8 of clubs")
    assert person["intention"] == "Kill you"
    assert person["weapon_type"] == "Melee"
    rook = format_rook_opponent("5 of hearts", "Ace of clubs", "10 of diamonds", "3 of spades")
    assert rook["body_type"] == "Attack"
    assert rook["magic_type"] == "Electric"
    print("validate_colostle_curated: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
