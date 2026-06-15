#!/usr/bin/env python3
"""Validate Brambletrek 2 curated YAML tables."""

from __future__ import annotations

import re
import subprocess
import sys
import types
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

PDF_PATH = ROOT / "docs/brambletrek_2/Brambletrek_2_-_Tales_in_the_Hundred_Acre_Woods.pdf"


def _bootstrap_bt2_imports() -> None:
    """Import BT2 curated without loading src.games.registry (other games may be broken)."""
    if "src.games.brambletrek_2.curated" in sys.modules:
        return
    src = types.ModuleType("src")
    src.__path__ = [str(ROOT / "src")]
    sys.modules["src"] = src
    games = types.ModuleType("src.games")
    games.__path__ = [str(ROOT / "src/games")]
    sys.modules["src.games"] = games
    bt2 = types.ModuleType("src.games.brambletrek_2")
    bt2.__path__ = [str(ROOT / "src/games/brambletrek_2")]
    sys.modules["src.games.brambletrek_2"] = bt2
    importlib.import_module("src.games.brambletrek_2.curated")


_bootstrap_bt2_imports()
from src.games.brambletrek_2.curated import (  # noqa: E402
    _ALL_RANKS,
    _arrival_table,
    _exploration_tables,
    _hollow_entry,
    _hollow_exit,
    _hollow_tables,
    _items_table,
    _legacies_data,
    _opponent_tactics,
    _opponents,
    _player_tactics,
    _recovery_tables,
    lookup_exploration_event,
    lookup_hollow_event,
    lookup_item,
    lookup_opponent_by_rank,
    lookup_player_tactic,
    parse_playing_card,
)

SUITS = ("hearts", "diamonds", "spades", "clubs")
LEGACY_IDS = [
    "bramble", "pooh", "piglet", "eeyore", "tigger", "owl", "rabbit", "kanga_roo",
    "salvager", "snoozer", "shadowcaster", "smasher", "singer", "snickerer", "solver", "sleeptalker",
]
LEGACY_PAGE_MAP = {
    18: "bramble", 19: "pooh", 20: "piglet", 21: "eeyore", 22: "tigger", 23: "owl",
    24: "rabbit", 25: "kanga_roo", 26: "salvager", 27: "snoozer", 28: "shadowcaster",
    29: "smasher", 30: "singer", 31: "snickerer", 32: "solver", 33: "sleeptalker",
}


def test_parse_virtual_deck() -> None:
    for card in ("J of hearts", "9 of spades", "Ace of diamonds", "10 of clubs"):
        assert parse_playing_card(card), card


def test_exploration_all_ranks() -> None:
    tables = _exploration_tables()
    missing = []
    for suit in SUITS:
        for rk in _ALL_RANKS:
            if rk not in (tables.get(suit) or {}):
                missing.append(f"{suit}.{rk}")
    assert not missing, f"missing exploration ranks: {missing[:10]}..."


def test_hollow_all_ranks() -> None:
    tables = _hollow_tables()
    for suit in SUITS:
        for rk in _ALL_RANKS:
            assert (tables.get(suit) or {}).get(rk), f"hollow {suit} {rk}"


def test_items_all_ranks() -> None:
    items = (_items_table().get("items") or {})
    for rk in _ALL_RANKS:
        assert items.get(rk), f"item {rk}"


def test_recovery_bands() -> None:
    for stat in ("health", "morale", "supplies"):
        bands = _recovery_tables().get(stat) or {}
        for band in ("2-4", "5-7", "8-10", "jack-queen", "king-ace"):
            assert bands.get(band), f"{stat} {band}"


def test_legacies() -> None:
    leg = _legacies_data().get("legacies") or {}
    assert len(leg) >= 16
    for lid in LEGACY_IDS:
        assert leg.get(lid), lid


def test_player_tactics() -> None:
    pt = (_player_tactics().get("player_tactics") or {})
    for lid in LEGACY_IDS:
        row = pt.get(lid) or {}
        assert len(row) >= 10, f"{lid} only {len(row)} tactics"


def test_opponents() -> None:
    by_rank = (_opponents().get("by_rank") or {})
    for rk in _ALL_RANKS:
        assert by_rank.get(rk), f"opponent rank {rk}"
    foes = (_opponent_tactics().get("opponents") or {})
    assert len(foes) >= 10, f"only {len(foes)} opponent tactic tables"


def test_arrival_bands() -> None:
    bands = (_arrival_table().get("bands") or {})
    for band in ("ace", "2-4", "5-7", "8-10", "jack", "queen", "king"):
        row = bands.get(band) or {}
        label = str(row.get("label", ""))
        assert label, f"missing arrival {band}"
        assert len(label) >= 60, f"arrival {band} too short ({len(label)} chars)"
        assert label.rstrip().endswith((".", "!", "?", "…")), f"arrival {band} truncated?"


def test_hollow_entry_exit() -> None:
    entry = (_hollow_entry().get("entry") or {})
    exit_rows = (_hollow_exit().get("exit") or {})
    for rk in _ALL_RANKS:
        assert entry.get(rk), f"hollow entry {rk}"
        assert exit_rows.get(rk), f"hollow exit {rk}"
        assert len(str(entry[rk].get("label", ""))) >= 40
        assert len(str(exit_rows[rk].get("label", ""))) >= 40


def test_legacy_abilities_complete() -> None:
    leg = (_legacies_data().get("legacies") or {})
    for lid in LEGACY_IDS:
        meta = leg.get(lid) or {}
        for ab in meta.get("abilities") or []:
            desc = str(ab.get("description", ""))
            assert len(desc) >= 40, f"{lid}/{ab.get('id')} description too short"
            assert desc.rstrip().endswith("."), f"{lid}/{ab.get('id')} missing period"


def test_legacy_stats_vs_pdf() -> None:
    try:
        import fitz
    except ImportError:
        return
    if not PDF_PATH.is_file():
        return
    doc = fitz.open(str(PDF_PATH))
    leg = (_legacies_data().get("legacies") or {})
    for page, lid in LEGACY_PAGE_MAP.items():
        text = doc[page - 1].get_text()
        spread = next(
            (ln.strip() for ln in text.splitlines() if "HEALTH" in ln and "SUPPLIES" in ln),
            "",
        )
        h = re.search(r"(\d+)\s*HEALTH", spread, re.I)
        s = re.search(r"(\d+)\s*SUPPLIES", spread, re.I)
        m = re.search(r"(\d+)\s*MORALE", spread, re.I)
        assert h and s and m, f"PDF spread missing for {lid} p{page}"
        pdf_stats = (int(h.group(1)), int(s.group(1)), int(m.group(1)))
        cur = leg.get(lid) or {}
        yaml_stats = (int(cur.get("health", 0)), int(cur.get("supplies", 0)), int(cur.get("morale", 0)))
        assert pdf_stats == yaml_stats, f"{lid} stats pdf={pdf_stats} yaml={yaml_stats}"


def test_no_watermark_in_tables() -> None:
    import yaml

    files = [
        "brambletrek_2_player_tactics.yaml",
        "brambletrek_2_opponent_tactics.yaml",
        "brambletrek_2_hollow_tables.yaml",
        "brambletrek_2_exploration_tables.yaml",
    ]
    blob = ""
    for name in files:
        blob += (ROOT / "data/curated" / name).read_text(encoding="utf-8")
    assert "Order #" not in blob
    assert "Lauri Mukkala" not in blob


def test_combined_draws() -> None:
    ev = lookup_exploration_event("J of hearts")
    assert ev and ev.get("label")
    hol = lookup_hollow_event("5 of diamonds")
    assert hol
    item = lookup_item("A of spades")
    assert item
    opp = lookup_opponent_by_rank("6 of clubs")
    assert opp and opp.get("id")
    tac = lookup_player_tactic("pooh", "3 of hearts")
    assert tac or lookup_player_tactic("bramble", "3 of hearts")


def test_extract_check() -> None:
    script = ROOT / "scripts/extract_brambletrek_2_pdf.py"
    result = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def main() -> int:
    tests = [
        test_parse_virtual_deck,
        test_exploration_all_ranks,
        test_hollow_all_ranks,
        test_items_all_ranks,
        test_recovery_bands,
        test_legacies,
        test_player_tactics,
        test_opponents,
        test_arrival_bands,
        test_hollow_entry_exit,
        test_legacy_abilities_complete,
        test_legacy_stats_vs_pdf,
        test_no_watermark_in_tables,
        test_combined_draws,
        test_extract_check,
    ]
    for fn in tests:
        fn()
        print(f"ok {fn.__name__}")
    print("validate_brambletrek_2_curated: all passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
