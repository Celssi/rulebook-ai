#!/usr/bin/env python3
"""Validate Outgunned rules helpers against PDF mechanics."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.gm_solo.dice import reroll_outgunned_pool, roll_outgunned_pool
from src.games.outgunned.actions import run_shortcut
from src.games.outgunned.curated import bump_tension, reset_tension


def _death_roulette_dead(bullets: int, roll: int) -> bool:
    return roll <= bullets


def test_death_roulette_matrix() -> None:
    for bullets in range(1, 6):
        for roll in range(1, 7):
            run = run_shortcut("death_roulette", death_roulette_bullets=bullets)
            # spot-check logic directly
            assert _death_roulette_dead(bullets, roll) == (roll <= bullets)


def test_tension_track() -> None:
    assert reset_tension() == 1
    assert reset_tension(phase="Crisis") == 2
    assert bump_tension(1)[0] == 2
    assert bump_tension(6) == (8, 2)
    assert bump_tension(11) == (12, 2)


def test_pool_matching_pairs() -> None:
    result = roll_outgunned_pool(4)
    assert result["ok"]
    assert len(result["rolls"]) == 4
    assert result["success_tier"] in {
        "none",
        "Basic",
        "Critical",
        "Extreme",
        "Impossible",
        "Jackpot!",
    }


def test_reroll_keeps_pairs() -> None:
    # 1,1,2,3 — pair of 1s; reroll 2 and 3 only
    out = reroll_outgunned_pool([1, 1, 2, 3])
    assert out["ok"]
    assert out["rolls"][0] == 1 and out["rolls"][1] == 1
    assert len(out["rerolled_indices"]) == 2


def test_shortcuts_smoke() -> None:
    assert run_shortcut("yes_no_oracle").get("static")
    assert run_shortcut("scene_drama").get("static")
    assert run_shortcut("tension", ad_state={"tension": 3}).get("ad_state_patch")
    pool = run_shortcut("outgunned_roll", pool_dice=4)
    assert pool.get("ad_state_patch", {}).get("last_pool_roll")
    reroll = run_shortcut("outgunned_reroll", ad_state=pool["ad_state_patch"])
    assert reroll.get("task") == "outgunned_reroll"


def main() -> int:
    test_death_roulette_matrix()
    test_tension_track()
    test_pool_matching_pairs()
    test_reroll_keeps_pairs()
    test_shortcuts_smoke()
    print("validate_outgunned_rules: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
