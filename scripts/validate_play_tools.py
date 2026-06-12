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
    deck_scope_key,
    draw_cards,
    normalize_card_name,
    parse_dice_expression,
    register_physical_card,
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
    scope = deck_scope_key(gid)
    reset_deck(game_id=gid)
    first = draw_cards(count=1, game_id=gid)
    assert first["ok"] is True
    assert len(first["cards"]) == 1
    remaining = first["remaining"]
    assert remaining == 51

    while deck_remaining(scope) > 0:
        draw_cards(count=1, game_id=gid)
    depleted = draw_cards(count=1, game_id=gid)
    assert depleted["ok"] is False

    reset_deck(game_id=gid)
    assert deck_remaining(scope) == 52
    clear_deck_store()


def test_scoped_deck() -> None:
    clear_deck_store()
    reset_deck(game_id="brambletrek", char_id="char_a")
    reset_deck(game_id="brambletrek", char_id="char_b")
    draw_cards(count=1, game_id="brambletrek", char_id="char_a")
    assert deck_remaining(deck_scope_key("brambletrek", "char_a")) == 51
    assert deck_remaining(deck_scope_key("brambletrek", "char_b")) == 52
    clear_deck_store()


def test_physical_card() -> None:
    clear_deck_store()
    reset_deck(game_id="brambletrek", char_id="c1")
    reg = register_physical_card("Queen of Hearts", game_id="brambletrek", char_id="c1")
    assert reg["ok"] is True
    assert deck_remaining(deck_scope_key("brambletrek", "c1")) == 51
    assert normalize_card_name("Q♥") is not None
    clear_deck_store()


def main() -> int:
    test_dice_parser()
    test_roll_dice()
    test_deck()
    test_scoped_deck()
    test_physical_card()
    print("All play-tool checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
