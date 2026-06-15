#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.ashes.curated import (
    all_ranks_valid,
    ember_for_level,
    format_enemy_draw,
    format_journal_draw,
    format_room_draw,
    format_trial_draw,
    lookup_enemy,
    lookup_room,
    lookup_starting_weapon,
    lookup_trial,
    parse_playing_card,
    prompt_set_options,
    trial_color,
)


def main() -> int:
    assert all_ranks_valid()
    assert parse_playing_card("J of hearts")["rank_key"] == "jack"
    # PDF p.57 — Puzzle room on ace
    room = lookup_room("ace")
    assert room["room"] == "Puzzle"
    assert room["check"] == "INT"
    # PDF p.57 — Titan of Kald on ace
    assert lookup_enemy("ace") == "Titan of Kald"
    draw = format_room_draw("4 of spades")
    assert draw["room"] == "Broken Door"
    assert draw["check"] == "PWR"
    journal = format_journal_draw("Queen of diamonds")
    assert "basin" in journal["event"].lower() or "skull" in journal["event"].lower()
    spirit = format_journal_draw("2 of hearts", prompt_set="spirit")
    assert spirit["prompt_set"] == "spirit"
    moon = format_journal_draw("ace of diamonds", prompt_set="moon")
    assert moon["prompt_set"] == "moon" and moon["event"]
    flame = format_journal_draw("king of clubs", prompt_set="flame")
    assert flame["prompt_set"] == "flame"
    assert spirit["event"]
    enemy = format_enemy_draw("5 of clubs")
    assert enemy["enemy"] == "Rogue of Crimson"
    assert trial_color("hearts") == "red"
    assert trial_color("clubs") == "black"
    assert lookup_trial("ace", "red")
    trial = format_trial_draw("King of spades")
    assert trial["color"] == "black" and trial["trial"]
    assert ember_for_level(1) == 3
    assert lookup_starting_weapon("melee", 1)
    sets = prompt_set_options()
    assert len(sets) == 10
    assert any(s["id"] == "crypt" for s in sets)
    assert any(s["id"] == "moon" for s in sets)
    assert any(s["label"] == "Path of the Moon" for s in sets)
    print("validate_ashes_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
