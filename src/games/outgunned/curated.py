"""Curated Outgunned Assistant Director tables."""

from __future__ import annotations

import random
from functools import lru_cache
from typing import Any, Literal

import yaml

from src.settings import CURATED_DIR

HurdleVariant = Literal["adventure", "core"]


def _load_yaml(name: str = "outgunned_ad_prompts.yaml") -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _tables() -> dict[str, Any]:
    return _load_yaml()


@lru_cache(maxsize=1)
def _roles_tables() -> dict[str, Any]:
    return _load_yaml("outgunned_roles.yaml")


def ad_prompt_entries() -> list[dict[str, str]]:
    entries = _tables().get("ad_prompts") or []
    return [e for e in entries if isinstance(e, dict) and e.get("text")]


def scene_prompt_entries() -> list[dict[str, Any]]:
    entries = _tables().get("scene_prompts") or []
    return [e for e in entries if isinstance(e, dict) and e.get("text")]


def lookup_table(name: str, key: str) -> str:
    table = _tables().get(name) or {}
    if not isinstance(table, dict):
        return ""
    val = table.get(str(key))
    if isinstance(val, str):
        return val
    return ""


def lookup_mission(key: str) -> dict[str, str]:
    table = _tables().get("mission_generator") or {}
    row = table.get(str(key)) if isinstance(table, dict) else None
    if not isinstance(row, dict):
        return {}
    return {
        "type": str(row.get("type", "") or ""),
        "complication": str(row.get("complication", "") or ""),
    }


def roll_villain_traits() -> dict[str, str]:
    return {
        "nature": lookup_table("villain_nature", str(random.randint(1, 6))),
        "desire": lookup_table("villain_desire", str(random.randint(1, 6))),
        "problem": lookup_table("villain_problem", str(random.randint(1, 6))),
    }


def roll_scene_prompt() -> dict[str, Any]:
    entries = scene_prompt_entries()
    if not entries:
        return {"roll": 0, "text": "Under Attack: An Enemy ambushes you."}
    return random.choice(entries)


def roll_scene_drama() -> dict[str, str]:
    drama = _tables().get("scene_drama") or {}
    if not isinstance(drama, dict):
        return {"subject": "Enemy", "sense": "Dangerous", "snag": "Combat"}
    out: dict[str, str] = {}
    for col in ("subject", "sense", "snag"):
        table = drama.get(col) or {}
        key = str(random.randint(1, 6))
        out[col] = table.get(key, "") if isinstance(table, dict) else ""
    return out


def roll_ad_prompt() -> dict[str, str | int]:
    """Scene prompt (d6 table), optional drama or climax inspiration."""
    roll = random.random()
    if roll < 0.12:
        drama = roll_scene_drama()
        text = (
            f"Scene Drama — Subject: {drama['subject']}, "
            f"Sense: {drama['sense']}, Snag: {drama['snag']}"
        )
        return {"category": "drama", "text": text, **drama}
    if roll < 0.18:
        climax = roll_climax()
        text = f"Climax check: does this Scene overcome the Phase Hurdle and reach the Aim? Consider: {climax}"
        return {"category": "climax", "text": text, "climax": climax}
    scene = roll_scene_prompt()
    return {
        "category": "scene",
        "text": str(scene.get("text", "") or ""),
        "roll": int(scene.get("roll", 0) or 0),
    }


def roll_hurdle(*, variant: HurdleVariant = "adventure") -> str:
    table_name = "hurdles_adventure" if variant == "adventure" else "hurdles"
    return lookup_table(table_name, str(random.randint(1, 6)))


def roll_climax() -> str:
    return lookup_table("climaxes", str(random.randint(1, 6)))


def roll_yes_no(*, likely: bool = False, unlikely: bool = False) -> dict[str, Any]:
    rolls = [random.randint(1, 6)]
    if likely or unlikely:
        rolls.append(random.randint(1, 6))
    chosen = max(rolls) if likely else min(rolls) if unlikely else rolls[0]
    answer = lookup_table("yes_no", str(chosen))
    return {"roll": chosen, "rolls": rolls, "answer": answer}


def roll_mission() -> dict[str, str]:
    key = str(random.randint(1, 6))
    mission = lookup_mission(key)
    return {"roll": key, **mission}


def role_entries() -> list[dict[str, Any]]:
    roles = _roles_tables().get("roles") or []
    return [r for r in roles if isinstance(r, dict) and r.get("id")]


def trope_entries() -> list[dict[str, Any]]:
    tropes = _roles_tables().get("tropes") or []
    return [t for t in tropes if isinstance(t, dict) and t.get("id")]


def lookup_role(role_id: str) -> dict[str, Any]:
    for row in role_entries():
        if str(row.get("id", "")) == role_id:
            return dict(row)
    return {}


def lookup_trope(trope_id: str) -> dict[str, Any]:
    for row in trope_entries():
        if str(row.get("id", "")) == trope_id:
            return dict(row)
    return {}


def attribute_ids() -> list[str]:
    attrs = _roles_tables().get("attributes") or []
    return [str(a) for a in attrs if a]


def skill_ids() -> list[str]:
    skills = _roles_tables().get("skills") or []
    return [str(s) for s in skills if s]


def age_options() -> list[str]:
    ages = _roles_tables().get("ages") or ["Young", "Adult", "Old"]
    return [str(a) for a in ages]


def bump_tension(current: int, *, phase: str = "") -> tuple[int, int]:
    """Return (new_tension, delta). AD s. 50."""
    tension = max(0, min(12, int(current or 0)))
    delta = 2 if tension >= 6 else 1
    return min(12, tension + delta), delta


def reset_tension(*, phase: str = "") -> int:
    """Start-of-Shot tension. Crisis/Showdown begin at 2."""
    if phase in ("Crisis", "Showdown"):
        return 2
    return 1


def all_ad_prompts_valid() -> bool:
    return len(scene_prompt_entries()) >= 6 and bool(_tables().get("scene_drama"))
