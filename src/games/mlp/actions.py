"""MLP shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.mlp.curated import ladder_index_to_id, skills_by_essence
from src.games.mlp.dice import (
    ladder_downshift,
    ladder_upshift,
    roll_skill_test,
    spellcasting_total_index,
)

GAME_MLP = "mlp"

ShortcutKind = Literal["roll", "roll_rag", "rag_only"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "skill_test", "label": "Skill Test (d20 + skill die)", "kind": "roll_rag"},
    {"id": "pay_spell_cost", "label": "Pay spell cost (downshift)", "kind": "roll"},
    {"id": "recover_spellcasting", "label": "Recover spellcasting (+1)", "kind": "roll"},
    {"id": "friendship_points", "label": "Friendship Points", "kind": "rag_only"},
    {"id": "encounter", "label": "Encounter", "kind": "rag_only"},
    {"id": "rules_help", "label": "MLP rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def _skill_label(skill_id: str) -> str:
    for group in skills_by_essence().values():
        for sk in group:
            if sk["id"] == skill_id:
                return sk["label"]
    return skill_id.replace("_", " ").title()


def match_mlp_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if "skill test" in lower or "skill check" in lower or "d20 check" in lower:
        return "skill_test"
    if "spell cost" in lower or "pay spell" in lower or "cast spell" in lower:
        return "pay_spell_cost"
    if "recover spell" in lower or "magic shift" in lower or "spellcasting recover" in lower:
        return "recover_spellcasting"
    if "friendship point" in lower or "friendship help" in lower or "friendship token" in lower:
        return "friendship_points"
    if "encounter" in lower and ("ponyville" in lower or "mlp" in lower or "pony" in lower):
        return "encounter"
    if lower.strip() == "encounter":
        return "encounter"
    if "mlp rules" in lower or "pony rules" in lower or "how to play mlp" in lower:
        return "rules_help"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_MLP,
    pony_name: str = "",
    origin: str = "",
    role: str = "",
    influences: list[str] | None = None,
    skills: dict[str, int] | None = None,
    default_skill_id: str = "alertness",
    default_dif: int = 15,
    edge_snag: str = "normal",
    spellcasting_rank: int = 0,
    spellcasting_current: int = 0,
    spell_cost: int = 1,
    friendship_points: int = 1,
    **_kwargs,
) -> dict:
    _ = game_id
    who = pony_name or "the pony"
    origin_note = f" ({origin.replace('_', ' ')})" if origin else ""
    inf_note = ""
    if influences:
        inf_note = f" Influences: {', '.join(influences)}."

    es = edge_snag if edge_snag in ("normal", "edge", "snag") else "normal"
    skill_map = skills or {}
    skill_id = default_skill_id or "alertness"
    skill_rank = int(skill_map.get(skill_id, 0) or 0)
    skill_name = _skill_label(skill_id)
    dif = int(default_dif or 15)

    if shortcut_id in ("skill_check", "skill_test"):
        result = roll_skill_test(skill_rank, dif, edge_snag=es, skill_name=skill_name)
        user = f"**Skill Test** — {who}{origin_note}{inf_note}\n\n{result['summary']}"
        prompt = (
            f"My Little Pony RPG Skill Test for {who}{origin_note}.{inf_note} "
            f"{result['summary']}. Explain DIF, success, Critical Success, and Fumble per the core rulebook."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "dice": result,
            "task": "skill_test",
        }

    if shortcut_id == "pay_spell_cost":
        cost = max(1, min(6, int(spell_cost or 1)))
        total_idx = spellcasting_total_index(spellcasting_rank) if spellcasting_rank else 0
        current = int(spellcasting_current or total_idx)
        new_current = ladder_downshift(current, cost)
        step_before = ladder_index_to_id(current)
        step_after = ladder_index_to_id(new_current)
        user = (
            f"**Pay spell cost** — {who}\n\n"
            f"Spellcasting downshift **{cost}**: **{step_before}** → **{step_after}**"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "pay_spell_cost",
            "new_spellcasting_current": new_current,
        }

    if shortcut_id in ("magic_shift", "recover_spellcasting"):
        total_idx = spellcasting_total_index(spellcasting_rank) if spellcasting_rank else 0
        current = int(spellcasting_current or total_idx)
        new_current = ladder_upshift(current, 1, cap_index=total_idx)
        step_before = ladder_index_to_id(current)
        step_after = ladder_index_to_id(new_current)
        user = (
            f"**Recover spellcasting** — {who}\n\n"
            f"Upshift +1: **{step_before}** → **{step_after}**"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "recover_spellcasting",
            "new_spellcasting_current": new_current,
        }

    if shortcut_id in ("friendship_help", "friendship_points"):
        prompt = (
            f"My Little Pony RPG Friendship Points for {who}. "
            f"Current pool: {friendship_points}. "
            "Explain the shared Friendship Point pool, how to spend points "
            "(re-roll 1s, temporary Specialization, +5 Defense, GM hint), "
            "and how solo play can treat NPC friends as the group. Cite the core rulebook."
        )
        return {"user_message": "**Friendship Points**", "prompt": prompt, "rag_only": True}

    if shortcut_id == "encounter":
        prompt = (
            f"Suggest a random encounter for {who} in Ponyville or Equestria "
            "using the Encounters in Ponyville supplement. "
            "Give a brief scene hook and any mechanical notes. Cite sources."
        )
        return {"user_message": "**Encounter**", "prompt": prompt, "rag_only": True}

    if shortcut_id == "rules_help":
        prompt = (
            "Explain how to play My Little Pony RPG (Renegade core) solo: "
            "Origins, Influences, Roles, Essences, Skills, Skill Tests (d20 + skill die vs DIF), "
            "Edge/Snag, Spellcasting and Magic Shift tracking, Friendship Points, and encounters. "
            "Cite the core rulebook."
        )
        return {"user_message": "**MLP rules**", "prompt": prompt, "rag_only": True}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
