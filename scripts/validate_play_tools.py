#!/usr/bin/env python3
"""Validate dice parser and deck behavior (no Ollama required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.play_tools import (
    clear_deck_store,
    deck_remaining,
    draw_cards,
    parse_dice_expression,
    reset_deck,
    roll_dice,
)


def test_dice_parser() -> None:
    assert parse_dice_expression("d20") == (1, 20, 0)
    assert parse_dice_expression("2d6+1") == (2, 6, 1)
    assert parse_dice_expression("3D8-2") == (3, 8, -2)
    assert isinstance(parse_dice_expression("bad"), str)


def test_roll_dice() -> None:
    r = roll_dice("2d6")
    assert r["ok"] is True
    assert len(r["rolls"]) == 2
    assert 2 <= r["total"] <= 12
    bad = roll_dice("not-dice")
    assert bad["ok"] is False


def test_deck() -> None:
    clear_deck_store()
    gid = "test_game"
    reset_deck(game_id=gid)
    first = draw_cards(count=1, game_id=gid)
    assert first["ok"] is True
    assert len(first["cards"]) == 1
    remaining = first["remaining"]
    assert remaining == 51

    # Draw until empty
    while deck_remaining(gid) > 0:
        draw_cards(count=1, game_id=gid)
    depleted = draw_cards(count=1, game_id=gid)
    assert depleted["ok"] is False

    reset_deck(game_id=gid)
    assert deck_remaining(gid) == 52
    clear_deck_store()


def main() -> int:
    test_dice_parser()
    test_roll_dice()
    test_deck()
    print("All play-tool checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
