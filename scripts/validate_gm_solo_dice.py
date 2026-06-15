"""Validate GM solo dice helpers."""

from __future__ import annotations

from src.games.gm_solo.dice import (
    roll_advantage_d20,
    roll_death_saves,
    reroll_outgunned_pool,
    roll_outgunned_pool,
    roll_plot_dice,
    roll_tor_skill,
    roll_year_zero,
)


def main() -> None:
    d20 = roll_advantage_d20(2, advantage="advantage")
    assert d20["ok"] and d20["total"] >= 3
    ds = roll_death_saves()
    assert ds["ok"] and 1 <= ds["roll"] <= 20
    yz = roll_year_zero(3)
    assert yz["ok"] and len(yz["rolls"]) == 3
    plot = roll_plot_dice(2)
    assert plot["ok"] and len(plot["rolls"]) == 2
    og = roll_outgunned_pool(4)
    assert og["ok"] and len(og["rolls"]) == 4
    assert og["success_tier"] in {"none", "Basic", "Critical", "Extreme", "Impossible", "Jackpot!"}
    fixed = reroll_outgunned_pool([1, 1, 2, 3])
    assert fixed["ok"] and fixed["rolls"][0] == 1
    tor = roll_tor_skill(2)
    assert tor["ok"] and 1 <= tor["feat"] <= 12
    print("validate_gm_solo_dice: OK")


if __name__ == "__main__":
    main()
