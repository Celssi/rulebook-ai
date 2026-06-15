"""MLP character options and validation from curated YAML."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR

_OPTIONS_PATH = CURATED_DIR / "mlp_character_options.yaml"

ESSENCE_KEYS = ("strength", "speed", "smarts", "social")
DEFENSE_MAP = {
    "strength": "toughness",
    "speed": "evasion",
    "smarts": "willpower",
    "social": "cleverness",
}

RANK_TO_LADDER_ID = {
    0: "base_die",
    1: "d2",
    2: "d4",
    3: "d6",
    4: "d8",
    5: "d10",
    6: "d12",
}

LADDER_ID_TO_RANK = {v: k for k, v in RANK_TO_LADDER_ID.items()}


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    with _OPTIONS_PATH.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def origins() -> dict[str, dict[str, Any]]:
    return dict(_load().get("origins") or {})


def roles() -> dict[str, dict[str, Any]]:
    return dict(_load().get("roles") or {})


def influences() -> list[dict[str, Any]]:
    return list(_load().get("influences") or [])


def skills_by_essence() -> dict[str, list[dict[str, str]]]:
    return dict(_load().get("skills_by_essence") or {})


def skill_ranks() -> list[dict[str, Any]]:
    return list(_load().get("skill_ranks") or [])


def dif_presets() -> list[dict[str, Any]]:
    return list(_load().get("dif_presets") or [])


def ladder_steps() -> list[dict[str, Any]]:
    return list(_load().get("spellcasting_ladder") or [])


def ladder_ids() -> list[str]:
    return [str(s["id"]) for s in ladder_steps()]


def friendship_spend_options() -> list[dict[str, Any]]:
    return list(_load().get("friendship_spend") or [])


def level_1_essence_total() -> int:
    return int(_load().get("level_1_essence_total", 16))


def rank_to_ladder_index(rank: int) -> int:
    rank = max(0, min(6, int(rank)))
    lid = RANK_TO_LADDER_ID[rank]
    ids = ladder_ids()
    return ids.index(lid)


def ladder_index_to_id(index: int) -> str:
    ids = ladder_ids()
    return ids[max(0, min(len(ids) - 1, int(index)))]


def ladder_id_to_index(ladder_id: str) -> int:
    return ladder_ids().index(ladder_id)


def compute_defenses(essences: dict[str, int]) -> dict[str, int]:
    out: dict[str, int] = {}
    for essence, defense in DEFENSE_MAP.items():
        out[defense] = 10 + int(essences.get(essence, 0) or 0)
    return out


def skill_points_spent(skills: dict[str, int], essence: str) -> int:
    skill_ids = {s["id"] for s in skills_by_essence().get(essence, [])}
    return sum(int(skills.get(sid, 0) or 0) for sid in skill_ids)


def apply_origin_bonus(
    essences: dict[str, int],
    origin: str,
    *,
    origin_essence_target: str = "",
) -> dict[str, int]:
    """Add +1 origin bonus to target essence."""
    out = {k: int(essences.get(k, 0) or 0) for k in ESSENCE_KEYS}
    origin_data = origins().get(origin, {})
    options = list(origin_data.get("essence_bonus_options") or ESSENCE_KEYS)
    target = origin_essence_target if origin_essence_target in options else options[0]
    if target in out:
        out[target] += 1
    return out


def apply_role_bonuses(essences: dict[str, int], role: str) -> dict[str, int]:
    """Add +2 diamond and +1 gold role bonuses."""
    out = {k: int(essences.get(k, 0) or 0) for k in ESSENCE_KEYS}
    role_data = roles().get(role, {})
    diamond = str(role_data.get("diamond_essence", "") or "")
    gold = str(role_data.get("gold_essence", "") or "")
    if diamond in out:
        out[diamond] += 2
    if gold in out:
        out[gold] += 1
    return out


def recompute_essences(
    base_essences: dict[str, int],
    *,
    origin: str = "",
    origin_essence_target: str = "",
    role: str = "",
) -> dict[str, int]:
    base = {k: max(1, int(base_essences.get(k, 1) or 1)) for k in ESSENCE_KEYS}
    if origin:
        base = apply_origin_bonus(base, origin, origin_essence_target=origin_essence_target)
    if role:
        base = apply_role_bonuses(base, role)
    return base


def origin_derived(origin: str) -> dict[str, Any]:
    data = origins().get(origin, {})
    health = int(data.get("health", 2) or 2)
    movement = int(data.get("movement", 30) or 30)
    spellcasting = int(data.get("default_spellcasting_rank", 0) or 0)
    return {"health": health, "movement": movement, "default_spellcasting_rank": spellcasting}


def validate_level1_character(data: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty if OK)."""
    errors: list[str] = []
    essences = data.get("essences") or {}
    if not isinstance(essences, dict):
        errors.append("essences must be a dict")
        return errors

    total = sum(int(essences.get(k, 0) or 0) for k in ESSENCE_KEYS)
    expected = level_1_essence_total()
    if total != expected:
        errors.append(f"essence total must be {expected}, got {total}")

    for k in ESSENCE_KEYS:
        v = int(essences.get(k, 0) or 0)
        if v < 1:
            errors.append(f"{k} essence must be at least 1")

    skills = data.get("skills") or {}
    if isinstance(skills, dict):
        for essence in ESSENCE_KEYS:
            cap = int(essences.get(essence, 0) or 0)
            spent = skill_points_spent(skills, essence)
            if spent > cap:
                errors.append(f"{essence} skills spent {spent} but essence is {cap}")

    influences_list = data.get("influences") or []
    hang_ups = data.get("hang_ups") or []
    if isinstance(influences_list, list):
        n_inf = len(influences_list)
        if n_inf < 1:
            errors.append("at least one Influence required")
        if n_inf > 3:
            errors.append("at most 3 Influences")
        required_hang_ups = max(0, n_inf - 1)
        if isinstance(hang_ups, list) and len(hang_ups) < required_hang_ups:
            errors.append(f"need {required_hang_ups} Hang-Up(s) for {n_inf} Influences")

    origin = str(data.get("origin", "") or "")
    if origin and origin not in origins():
        errors.append(f"unknown origin: {origin}")

    role = str(data.get("role", "") or "")
    if role and role not in roles():
        errors.append(f"unknown role: {role}")

    return errors


def options_payload() -> dict[str, Any]:
    return {
        "origins": [{"id": k, **v} for k, v in origins().items()],
        "roles": [{"id": k, **v} for k, v in roles().items()],
        "influences": influences(),
        "skills_by_essence": skills_by_essence(),
        "skill_ranks": skill_ranks(),
        "dif_presets": dif_presets(),
        "spellcasting_ladder": ladder_steps(),
        "friendship_spend": friendship_spend_options(),
        "essence_keys": list(ESSENCE_KEYS),
        "level_1_essence_total": level_1_essence_total(),
        "player_essence_points": int(_load().get("level_1_essence_breakdown", {}).get("player_points", 12)),
    }
