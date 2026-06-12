#!/usr/bin/env python3
"""Validate dice parser and deck tool behavior (no Ollama required)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.tools import (  # noqa: E402
    clear_deck_store,
    draw_cards,
    parse_dice_expression,
    reset_deck,
    roll_dice,
)


def check_dice_parser() -> None:
    cases_ok = [
        ("d20", (1, 20, 0)),
        ("2d6", (2, 6, 0)),
        ("2d6+1", (2, 6, 1)),
        ("3D8-2", (3, 8, -2)),
    ]
    for expr, expected in cases_ok:
        got = parse_dice_expression(expr)
        assert got == expected, f"{expr!r}: expected {expected}, got {got}"

    for bad in ("", "2x6", "d1", "0d6", "101d6"):
        err = parse_dice_expression(bad)
        assert isinstance(err, str), f"{bad!r} should fail, got {err!r}"

    r = roll_dice("1d6")
    assert r["ok"] and len(r["rolls"]) == 1 and 1 <= r["rolls"][0] <= 6
    assert r["total"] == r["rolls"][0]

    bad_roll = roll_dice("not-dice")
    assert not bad_roll["ok"] and bad_roll["error"]


def check_deck() -> None:
    clear_deck_store()
    game_id = "test_validate"

    reset = reset_deck(game_id=game_id)
    assert reset["ok"] and reset["remaining"] == 52

    draw = draw_cards(count=3, game_id=game_id)
    assert draw["ok"] and len(draw["cards"]) == 3 and draw["remaining"] == 49

    reset_deck(game_id=game_id)
    for _ in range(52):
        d = draw_cards(count=1, game_id=game_id)
        assert d["ok"], d

    empty = draw_cards(count=1, game_id=game_id)
    assert not empty["ok"] and empty["remaining"] == 0

    again = reset_deck(game_id=game_id)
    assert again["remaining"] == 52

    clear_deck_store()


def check_rerank() -> None:
    from llama_index.core.schema import NodeWithScore, TextNode

    from src.retrieval_core import rerank_available, rerank_nodes

    nodes = [
        NodeWithScore(node=TextNode(text="Deep Strike deploys reserves"), score=0.1),
        NodeWithScore(node=TextNode(text="Morale recovery table"), score=0.2),
    ]
    unchanged = rerank_nodes("Deep Strike keyword", nodes, use_rerank=False)
    assert unchanged is nodes
    if rerank_available():
        ranked = rerank_nodes("Deep Strike keyword", list(nodes), use_rerank=True)
        assert len(ranked) == 2
        assert all(n.score is not None for n in ranked)


def main() -> int:
    check_dice_parser()
    check_deck()
    check_rerank()
    print("validate_tools: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
