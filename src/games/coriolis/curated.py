"""Curated Coriolis: The Great Dark tables."""

from __future__ import annotations

import random
from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _professions_data() -> dict[str, Any]:
    return _load_yaml("coriolis_professions.yaml")


@lru_cache(maxsize=1)
def _talents_data() -> dict[str, Any]:
    return _load_yaml("coriolis_talents.yaml")


@lru_cache(maxsize=1)
def _trauma_data() -> dict[str, Any]:
    return _load_yaml("coriolis_mental_trauma.yaml")


@lru_cache(maxsize=1)
def _encounters_data() -> dict[str, Any]:
    return _load_yaml("coriolis_encounters.yaml")


def profession_entries() -> list[dict[str, Any]]:
    entries = _professions_data().get("professions") or []
    return [e for e in entries if isinstance(e, dict) and e.get("id")]


def profession_by_id(profession_id: str) -> dict[str, Any]:
    pid = str(profession_id or "").strip()
    for entry in profession_entries():
        if str(entry.get("id", "")) == pid:
            return entry
    return {}


def profession_options() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for entry in profession_entries():
        specialties = entry.get("specialties") or []
        result.append(
            {
                "id": str(entry.get("id", "")),
                "label": str(entry.get("label", "") or entry.get("id", "")),
                "key_attribute": str(entry.get("key_attribute", "") or ""),
                "key_talents": list(entry.get("key_talents") or []),
                "specialties": [
                    {
                        "id": str(s.get("id", "")),
                        "label": str(s.get("label", "") or s.get("id", "")),
                        "free_talent": str(s.get("free_talent", "") or ""),
                    }
                    for s in specialties
                    if isinstance(s, dict) and s.get("id")
                ],
            }
        )
    return result


def specialty_for(profession_id: str, specialty_id: str) -> dict[str, str]:
    prof = profession_by_id(profession_id)
    sid = str(specialty_id or "").strip()
    for spec in prof.get("specialties") or []:
        if isinstance(spec, dict) and str(spec.get("id", "")) == sid:
            return {
                "id": sid,
                "label": str(spec.get("label", "") or sid),
                "free_talent": str(spec.get("free_talent", "") or ""),
            }
    return {}


def talent_options() -> list[dict[str, str]]:
    entries = _talents_data().get("talents") or []
    return [
        {
            "id": str(e.get("id", "")),
            "label": str(e.get("label", "") or e.get("id", "")),
            "category": str(e.get("category", "") or ""),
        }
        for e in entries
        if isinstance(e, dict) and e.get("id")
    ]


def crew_role_options() -> list[dict[str, str]]:
    entries = _professions_data().get("crew_roles") or []
    return [
        {"id": str(e.get("id", "")), "label": str(e.get("label", "") or e.get("id", ""))}
        for e in entries
        if isinstance(e, dict) and e.get("id")
    ]


def encounter_entries() -> list[dict[str, str]]:
    entries = _encounters_data().get("encounters") or []
    return [e for e in entries if isinstance(e, dict) and e.get("text")]


def roll_encounter() -> dict[str, str]:
    entries = encounter_entries()
    if not entries:
        return {
            "category": "delve",
            "text": "A distress beacon flickers in the Lost Horizon between stations.",
        }
    pick = random.choice(entries)
    return {
        "category": str(pick.get("category", "delve") or "delve"),
        "text": str(pick.get("text", "") or ""),
    }


def _roll_d66() -> int:
    tens = random.randint(1, 6)
    ones = random.randint(1, 6)
    return tens * 10 + ones


def roll_mental_trauma() -> dict[str, Any]:
    roll = _roll_d66()
    table = _trauma_data().get("trauma") or {}
    key = str(roll)
    entry = table.get(key) if isinstance(table, dict) else None
    if not isinstance(entry, dict):
        entry = {"label": "Unknown trauma", "effect": "Consult the rulebook."}
    label = str(entry.get("label", "") or "Trauma")
    effect = str(entry.get("effect", "") or "")
    return {
        "roll": roll,
        "label": label,
        "effect": effect,
        "summary": f"Mental trauma D66 = **{roll}** — {label}: {effect}",
    }


def roll_despair_resist(
    empathy: int,
    *,
    potential_despair: int = 1,
    pushed: bool = False,
) -> dict[str, Any]:
    """EMPATHY roll to resist external despair (core rulebook p. 68)."""
    from src.games.gm_solo.dice import roll_great_dark

    pool = max(1, int(empathy))
    dice = roll_great_dark(pool, gear_pool=0, pushed=pushed)
    successes = int(dice.get("successes", 0) or 0)
    despair_taken = max(0, int(potential_despair) - successes)
    hope_loss_from_push = int(dice.get("base_ones", 0) or 0) if pushed else 0
    summary = (
        f"Despair resist (EMPATHY {pool}): {dice['summary']} — "
        f"**{successes}** successes cancel despair; "
        f"**{despair_taken}** despair taken"
    )
    if hope_loss_from_push:
        summary += f"; push costs **{hope_loss_from_push}** Hope from base 1s"
    return {
        "dice": dice,
        "successes": successes,
        "despair_taken": despair_taken,
        "hope_loss_from_push": hope_loss_from_push,
        "summary": summary,
        "potential_despair": int(potential_despair),
    }


def all_professions_valid() -> bool:
    return len(profession_entries()) == 8


def all_encounters_valid() -> bool:
    return len(encounter_entries()) >= 4


def all_trauma_valid() -> bool:
    table = _trauma_data().get("trauma") or {}
    return isinstance(table, dict) and len(table) >= 30
