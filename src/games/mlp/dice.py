"""MLP Essence20 dice mechanics."""

from __future__ import annotations

import random
from typing import Any, Literal

from src.games.mlp.curated import ladder_ids, ladder_index_to_id, rank_to_ladder_index

EdgeSnag = Literal["normal", "edge", "snag"]

RANK_DICE = {
    0: None,
    1: 2,
    2: 4,
    3: 6,
    4: 8,
    5: 10,
    6: 12,
}


def _roll_d20(edge_snag: EdgeSnag = "normal") -> tuple[int, list[int]]:
    if edge_snag == "edge":
        rolls = [random.randint(1, 20), random.randint(1, 20)]
        return max(rolls), rolls
    if edge_snag == "snag":
        rolls = [random.randint(1, 20), random.randint(1, 20)]
        return min(rolls), rolls
    roll = random.randint(1, 20)
    return roll, [roll]


def _roll_die(sides: int) -> int:
    return random.randint(1, sides)


def _skill_die_total(rank: int, *, specialization: bool = False) -> tuple[int, list[int]]:
    if rank <= 0:
        return 0, []
    sides = RANK_DICE[rank]
    if sides is None:
        return 0, []
    if specialization and rank >= 2:
        rolls = [_roll_die(s) for s in (RANK_DICE[r] for r in range(2, rank + 1) if RANK_DICE[r])]
        if not rolls:
            rolls = [_roll_die(sides)]
        return max(rolls), rolls
    roll = _roll_die(sides)
    return roll, [roll]


def _ladder_skill_total(step_id: str) -> tuple[int | None, list[int], str]:
    if step_id in ("critical_success", "auto_success"):
        return None, [], "auto_success"
    if step_id in ("auto_fail", "fumble"):
        return None, [], "auto_fail"
    if step_id == "base_die":
        return 0, [], "base_die"
    if step_id == "triple_d6":
        rolls = [_roll_die(6) for _ in range(3)]
        return sum(rolls), rolls, "dice"
    if step_id == "double_d8":
        rolls = [_roll_die(8) for _ in range(2)]
        return sum(rolls), rolls, "dice"
    if step_id.startswith("d"):
        sides = int(step_id[1:])
        roll = _roll_die(sides)
        return roll, [roll], "dice"
    return 0, [], "base_die"


def roll_skill_test(
    skill_rank: int,
    dif: int,
    *,
    edge_snag: EdgeSnag = "normal",
    specialization: bool = False,
    skill_name: str = "Skill",
) -> dict[str, Any]:
    dif = int(dif)
    skill_rank = max(0, min(6, int(skill_rank)))

    if skill_rank == 0:
        d20, d20_rolls = _roll_d20("snag")
        total = d20
        success = total >= dif
        fumble = d20 == 1 and not success
        summary = (
            f"**Skill Test** ({skill_name}, untrained) vs DIF **{dif}**\n\n"
            f"d20 (Snag): {d20_rolls} → kept **{d20}**\n\n"
            f"Total **{total}** — **{'Success' if success else 'Failure'}**"
            + (" (Fumble)" if fumble else "")
        )
        return {
            "ok": True,
            "d20": d20,
            "d20_rolls": d20_rolls,
            "skill_rolls": [],
            "skill_total": 0,
            "total": total,
            "dif": dif,
            "success": success,
            "critical": False,
            "fumble": fumble,
            "summary": summary,
        }

    d20, d20_rolls = _roll_d20(edge_snag)
    skill_total, skill_rolls = _skill_die_total(skill_rank, specialization=specialization)
    total = d20 + skill_total
    success = total >= dif
    critical = success and any(r == RANK_DICE[skill_rank] for r in skill_rolls if skill_rank >= 2)
    fumble = d20 == 1 and not success
    die_label = f"d{RANK_DICE[skill_rank]}"
    edge_note = f" ({edge_snag})" if edge_snag != "normal" else ""
    summary = (
        f"**Skill Test** ({skill_name} {die_label}) vs DIF **{dif}**{edge_note}\n\n"
        f"d20: {d20_rolls} → **{d20}** · {die_label}: {skill_rolls} → **{skill_total}**\n\n"
        f"Total **{total}** — **{'Success' if success else 'Failure'}**"
        + (" (Critical!)" if critical else "")
        + (" (Fumble)" if fumble else "")
    )
    return {
        "ok": True,
        "d20": d20,
        "d20_rolls": d20_rolls,
        "skill_rolls": skill_rolls,
        "skill_total": skill_total,
        "total": total,
        "dif": dif,
        "success": success,
        "critical": critical,
        "fumble": fumble,
        "summary": summary,
    }


def roll_spellcasting_test(
    ladder_index: int,
    dif: int,
    *,
    edge_snag: EdgeSnag = "normal",
) -> dict[str, Any]:
    dif = int(dif)
    step_id = ladder_index_to_id(ladder_index)
    skill_total, skill_rolls, mode = _ladder_skill_total(step_id)

    if mode == "auto_success":
        summary = f"**Spellcasting Test** ({step_id}) vs DIF **{dif}** — **Auto Success**"
        return {
            "ok": True,
            "ladder_step": step_id,
            "total": dif,
            "dif": dif,
            "success": True,
            "summary": summary,
        }
    if mode == "auto_fail":
        summary = f"**Spellcasting Test** ({step_id}) vs DIF **{dif}** — **Auto Fail**"
        return {
            "ok": True,
            "ladder_step": step_id,
            "total": 0,
            "dif": dif,
            "success": False,
            "summary": summary,
        }

    d20, d20_rolls = _roll_d20(edge_snag)
    total = d20 + (skill_total or 0)
    success = total >= dif
    edge_note = f" ({edge_snag})" if edge_snag != "normal" else ""
    skill_part = f" · skill dice {skill_rolls} → **{skill_total}**" if skill_rolls else ""
    summary = (
        f"**Spellcasting Test** ({step_id}) vs DIF **{dif}**{edge_note}\n\n"
        f"d20: {d20_rolls} → **{d20}**{skill_part}\n\n"
        f"Total **{total}** — **{'Success' if success else 'Failure'}**"
    )
    return {
        "ok": True,
        "ladder_step": step_id,
        "d20": d20,
        "skill_rolls": skill_rolls,
        "total": total,
        "dif": dif,
        "success": success,
        "summary": summary,
    }


def ladder_downshift(current_index: int, steps: int = 1) -> int:
    idx = max(0, min(len(ladder_ids()) - 1, int(current_index)))
    return max(0, min(len(ladder_ids()) - 1, idx + max(1, int(steps))))


def ladder_upshift(current_index: int, steps: int = 1, *, cap_index: int | None = None) -> int:
    idx = max(0, min(len(ladder_ids()) - 1, int(current_index)))
    cap = len(ladder_ids()) - 1 if cap_index is None else max(0, min(len(ladder_ids()) - 1, int(cap_index)))
    return max(cap, idx - max(1, int(steps)))


def spellcasting_total_index(rank: int) -> int:
    return rank_to_ladder_index(max(0, min(6, int(rank))))
