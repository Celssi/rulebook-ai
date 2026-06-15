"""Dice helpers for GM-led solo play systems."""

from __future__ import annotations

import random
from typing import Any, Literal

from src.play_tools import format_dice_result, roll_dice

Advantage = Literal["normal", "advantage", "disadvantage"]

_TOR_FEAT_ICONS = {
    11: "gandalf",
    12: "sauron",
}

_PLOT_D6 = {
    1: "complication",
    6: "opportunity",
}


def roll_advantage_d20(
    modifier: int = 0,
    *,
    advantage: Advantage = "normal",
) -> dict[str, Any]:
    if advantage == "advantage":
        a = roll_dice("1d20")
        b = roll_dice("1d20")
        rolls = [int(a["rolls"][0]), int(b["rolls"][0])]
        chosen = max(rolls)
        total = chosen + modifier
        summary = (
            f"d20 advantage: rolled {rolls[0]} and {rolls[1]}, kept {chosen}"
            + (f" {'+' if modifier >= 0 else ''}{modifier}" if modifier else "")
            + f" = **{total}**"
        )
        return {
            "ok": True,
            "rolls": rolls,
            "chosen": chosen,
            "modifier": modifier,
            "total": total,
            "summary": summary,
            "advantage": advantage,
        }
    if advantage == "disadvantage":
        a = roll_dice("1d20")
        b = roll_dice("1d20")
        rolls = [int(a["rolls"][0]), int(b["rolls"][0])]
        chosen = min(rolls)
        total = chosen + modifier
        summary = (
            f"d20 disadvantage: rolled {rolls[0]} and {rolls[1]}, kept {chosen}"
            + (f" {'+' if modifier >= 0 else ''}{modifier}" if modifier else "")
            + f" = **{total}**"
        )
        return {
            "ok": True,
            "rolls": rolls,
            "chosen": chosen,
            "modifier": modifier,
            "total": total,
            "summary": summary,
            "advantage": advantage,
        }
    result = roll_dice(f"1d20{modifier:+d}" if modifier else "1d20")
    return {
        "ok": True,
        "rolls": list(result.get("rolls", [])),
        "chosen": int(result.get("total", 0)) - modifier,
        "modifier": modifier,
        "total": int(result.get("total", 0)),
        "summary": format_dice_result(result),
        "advantage": advantage,
    }


def roll_death_saves() -> dict[str, Any]:
    result = roll_dice("1d20")
    roll = int(result["rolls"][0])
    if roll == 1:
        outcome = "two failures"
    elif roll == 20:
        outcome = "regain 1 HP and wake"
    elif roll >= 10:
        outcome = "success"
    else:
        outcome = "failure"
    return {
        "ok": True,
        "roll": roll,
        "outcome": outcome,
        "summary": f"Death save: **{roll}** — {outcome}",
    }


def roll_year_zero(pool: int, *, pushed: bool = False) -> dict[str, Any]:
    pool = max(1, min(20, int(pool)))
    rolls = [random.randint(1, 6) for _ in range(pool)]
    successes = sum(1 for r in rolls if r == 6)
    ones = sum(1 for r in rolls if r == 1)
    push_note = f" (pushed; {ones} stress from 1s)" if pushed and ones else ""
    summary = (
        f"Year Zero pool {pool}d6: {rolls} → **{successes}** success"
        f"{'es' if successes != 1 else ''}{push_note}"
    )
    return {
        "ok": True,
        "rolls": rolls,
        "successes": successes,
        "ones": ones,
        "pushed": pushed,
        "summary": summary,
    }


def roll_great_dark(
    base_pool: int,
    gear_pool: int = 0,
    *,
    pushed: bool = False,
) -> dict[str, Any]:
    """Coriolis: The Great Dark base + gear dice roll."""
    base_pool = max(1, min(20, int(base_pool)))
    gear_pool = max(0, min(10, int(gear_pool)))

    base_rolls = [random.randint(1, 6) for _ in range(base_pool)]
    gear_rolls = [random.randint(1, 6) for _ in range(gear_pool)] if gear_pool else []

    if pushed:
        reroll_base = [random.randint(1, 6) for r in base_rolls if r not in (1, 6)]
        reroll_gear = [random.randint(1, 6) for r in gear_rolls if r not in (1, 6)] if gear_rolls else []
        bi = 0
        for i, r in enumerate(base_rolls):
            if r not in (1, 6):
                base_rolls[i] = reroll_base[bi]
                bi += 1
        gi = 0
        for i, r in enumerate(gear_rolls):
            if r not in (1, 6):
                gear_rolls[i] = reroll_gear[gi]
                gi += 1

    all_rolls = base_rolls + gear_rolls
    successes = sum(1 for r in all_rolls if r == 6)
    base_ones = sum(1 for r in base_rolls if r == 1)
    gear_ones = sum(1 for r in gear_rolls if r == 1) if pushed else 0

    parts = [f"base {base_pool}d6: {base_rolls}"]
    if gear_pool:
        parts.append(f"gear {gear_pool}d6: {gear_rolls}")
    summary = "Great Dark roll — " + "; ".join(parts)
    summary += f" → **{successes}** success{'es' if successes != 1 else ''}"
    if pushed:
        if base_ones:
            summary += f"; **{base_ones}** base 1s (Hope loss)"
        if gear_ones:
            summary += f"; **{gear_ones}** gear 1s (gear penalty)"

    return {
        "ok": True,
        "rolls_base": base_rolls,
        "rolls_gear": gear_rolls,
        "rolls": all_rolls,
        "successes": successes,
        "base_ones": base_ones if pushed else 0,
        "gear_ones": gear_ones,
        "pushed": pushed,
        "summary": summary,
    }


def roll_plot_dice(count: int = 1) -> dict[str, Any]:
    count = max(1, min(10, int(count)))
    rolls = [random.randint(1, 6) for _ in range(count)]
    labels = []
    for r in rolls:
        if r in _PLOT_D6:
            labels.append(_PLOT_D6[r])
        else:
            labels.append("neutral")
    summary = f"Plot dice ({count}d6): {rolls}"
    if labels:
        summary += f" — {', '.join(labels)}"
    return {"ok": True, "rolls": rolls, "labels": labels, "summary": summary}


_TIER_RANK = {
    "none": 0,
    "Basic": 1,
    "Critical": 2,
    "Extreme": 3,
    "Impossible": 4,
    "Jackpot!": 5,
}


def _outgunned_success_tier(match_count: int) -> str:
    if match_count >= 6:
        return "Jackpot!"
    if match_count == 5:
        return "Impossible"
    if match_count == 4:
        return "Extreme"
    if match_count == 3:
        return "Critical"
    if match_count == 2:
        return "Basic"
    return "none"


def _analyze_outgunned_rolls(rolls: list[int]) -> dict[str, Any]:
    counts: dict[int, int] = {}
    for r in rolls:
        counts[r] = counts.get(r, 0) + 1
    groups = [(face, n) for face, n in counts.items() if n >= 2]
    groups.sort(key=lambda item: (-item[1], item[0]))
    best_tier = _outgunned_success_tier(groups[0][1]) if groups else "none"
    best_count = groups[0][1] if groups else 0
    detail = ", ".join(
        f"{_outgunned_success_tier(n)} ({n}×{face})" for face, n in groups
    )
    summary = f"Outgunned pool {len(rolls)}d6: {rolls}"
    if groups:
        summary += f" → **{best_tier}**" + (
            f" ({detail})" if len(groups) > 1 else f" ({best_count}×{groups[0][0]})"
        )
    else:
        summary += " → **failure** (no matching pairs)"
    return {
        "ok": True,
        "rolls": rolls,
        "success_tier": best_tier,
        "success_groups": [
            {"face": f, "count": n, "tier": _outgunned_success_tier(n)} for f, n in groups
        ],
        "summary": summary,
    }


def roll_outgunned_pool(dice: int = 3) -> dict[str, Any]:
    """Outgunned Adventure pool: successes from matching d6 faces (pairs+)."""
    dice = max(2, min(9, int(dice)))
    rolls = [random.randint(1, 6) for _ in range(dice)]
    return _analyze_outgunned_rolls(rolls)


def reroll_outgunned_pool(
    rolls: list[int],
    *,
    free_reroll: bool = False,
) -> dict[str, Any]:
    """Re-roll dice not part of a success combination (Adventure s. 72)."""
    if len(rolls) < 2:
        return {"ok": False, "summary": "Need a prior pool roll with at least 2 dice."}
    counts: dict[int, int] = {}
    for r in rolls:
        counts[r] = counts.get(r, 0) + 1
    reroll_indices = [i for i, r in enumerate(rolls) if counts[r] < 2]
    if not reroll_indices:
        return {
            "ok": False,
            "summary": "No dice to re-roll — every die is part of a success.",
            "rolls": list(rolls),
        }
    previous = _analyze_outgunned_rolls(list(rolls))
    new_rolls = list(rolls)
    for i in reroll_indices:
        new_rolls[i] = random.randint(1, 6)
    current = _analyze_outgunned_rolls(new_rolls)
    prev_rank = _TIER_RANK.get(previous["success_tier"], 0)
    new_rank = _TIER_RANK.get(current["success_tier"], 0)
    extra_group = len(current["success_groups"]) > len(previous["success_groups"])
    improved = new_rank > prev_rank or (
        new_rank == prev_rank and extra_group and new_rank > 0
    )
    lost_success = (
        not improved
        and not free_reroll
        and previous["success_tier"] != "none"
    )
    note = "Better result!" if improved else (
        "Free re-roll — kept prior success." if free_reroll and not improved
        else "Worse — lose one prior success." if lost_success
        else "No improvement."
    )
    summary = (
        f"Re-roll {len(reroll_indices)} die(s): {rolls} → {new_rolls} — "
        f"{previous['success_tier']} → **{current['success_tier']}** ({note})"
    )
    return {
        **current,
        "previous_rolls": list(rolls),
        "rerolled_indices": reroll_indices,
        "previous_tier": previous["success_tier"],
        "improved": improved,
        "lost_success": lost_success,
        "free_reroll": free_reroll,
        "summary": summary,
    }


def roll_tor_skill(success_dice: int = 1) -> dict[str, Any]:
    success_dice = max(0, min(20, int(success_dice)))
    feat = random.randint(1, 12)
    successes = [random.randint(1, 6) for _ in range(success_dice)]
    success_count = sum(1 for s in successes if s in (5, 6))
    icon = _TOR_FEAT_ICONS.get(feat, "")
    icon_note = ""
    if icon == "gandalf":
        icon_note = " — Gandalf rune (Fortune)"
    elif icon == "sauron":
        icon_note = " — Eye of Sauron (Ill-Fortune)"
    sd = f" + {successes}" if successes else ""
    summary = (
        f"TOR skill: Feat d12 = **{feat}**{icon_note}; "
        f"Success dice{sd} → **{success_count}** success{'es' if success_count != 1 else ''}"
    )
    return {
        "ok": True,
        "feat": feat,
        "feat_icon": icon,
        "success_rolls": successes,
        "success_count": success_count,
        "summary": summary,
    }
