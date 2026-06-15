"""Load D&D 5e curated character creation data."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR

from src.games.dnd5e.entity import CAMPAIGN_SETTING_OPTIONS

_SKILLS_PATH = CURATED_DIR / "dnd5e_skills.yaml"
_CLASSES_PATH = CURATED_DIR / "dnd5e_classes.yaml"
_SPECIES_PATH = CURATED_DIR / "dnd5e_species.yaml"
_BACKGROUNDS_PATH = CURATED_DIR / "dnd5e_backgrounds.yaml"
_SPELLS_PATH = CURATED_DIR / "dnd5e_spells.yaml"
_EQUIPMENT_PATH = CURATED_DIR / "dnd5e_equipment.yaml"


def _load(path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def skills_data() -> dict[str, Any]:
    return _load(_SKILLS_PATH)


@lru_cache(maxsize=1)
def classes_data() -> dict[str, Any]:
    return _load(_CLASSES_PATH)


@lru_cache(maxsize=1)
def species_data() -> dict[str, Any]:
    return _load(_SPECIES_PATH)


@lru_cache(maxsize=1)
def backgrounds_data() -> dict[str, Any]:
    return _load(_BACKGROUNDS_PATH)


@lru_cache(maxsize=1)
def spells_data() -> dict[str, Any]:
    return _load(_SPELLS_PATH)


@lru_cache(maxsize=1)
def equipment_data() -> dict[str, Any]:
    return _load(_EQUIPMENT_PATH)


def list_armor() -> list[dict[str, Any]]:
    return list(equipment_data().get("armor") or [])


def get_armor(armor_id: str) -> dict[str, Any] | None:
    for row in list_armor():
        if row.get("id") == armor_id:
            return row
    return None


def list_weapons() -> list[dict[str, Any]]:
    return list(equipment_data().get("weapons") or [])


def list_languages() -> list[str]:
    return [str(x) for x in (equipment_data().get("languages") or [])]


def shield_ac_bonus() -> int:
    return int(equipment_data().get("shield_ac", 2) or 2)


def list_classes() -> list[dict[str, Any]]:
    return list(classes_data().get("classes") or [])


def list_species() -> list[dict[str, Any]]:
    return list(species_data().get("species") or [])


def list_backgrounds() -> list[dict[str, Any]]:
    return list(backgrounds_data().get("backgrounds") or [])


def get_class(class_id: str) -> dict[str, Any] | None:
    for row in list_classes():
        if row.get("id") == class_id:
            return row
    return None


def get_species(species_id: str) -> dict[str, Any] | None:
    for row in list_species():
        if row.get("id") == species_id:
            return row
    return None


def get_background(background_id: str) -> dict[str, Any] | None:
    for row in list_backgrounds():
        if row.get("id") == background_id:
            return row
    return None


def spell_list_for(class_id: str) -> dict[str, list[str]]:
    lists = spells_data().get("spell_lists") or {}
    cls = get_class(class_id) or {}
    key = str(cls.get("spell_list") or class_id)
    raw = lists.get(key) or {}
    return {str(k): list(v or []) for k, v in raw.items() if isinstance(v, list)}


def full_caster_slots(level: int) -> dict[str, int]:
    table = classes_data().get("full_caster_slots") or {}
    row = table.get(str(max(1, min(20, int(level)))))
    if not isinstance(row, list):
        return {}
    return {str(i + 1): int(v) for i, v in enumerate(row) if int(v or 0) > 0}


def half_caster_slots(level: int) -> dict[str, int]:
    table = classes_data().get("half_caster_slots") or {}
    row = table.get(str(max(1, min(20, int(level)))))
    if not isinstance(row, list):
        return {}
    return {str(i + 1): int(v) for i, v in enumerate(row) if int(v or 0) > 0}


def character_options_payload() -> dict[str, Any]:
    skills = skills_data()
    return {
        "classes": list_classes(),
        "species": list_species(),
        "backgrounds": list_backgrounds(),
        "skills": skills.get("skills") or [],
        "alignments": skills.get("alignments") or [],
        "standard_array": skills.get("standard_array") or [15, 14, 13, 12, 10, 8],
        "standard_array_by_class": skills.get("standard_array_by_class") or {},
        "spell_lists": spells_data().get("spell_lists") or {},
        "campaign_settings": CAMPAIGN_SETTING_OPTIONS,
        "armor": list_armor(),
        "weapons": list_weapons(),
        "languages": list_languages(),
        "shield_ac": shield_ac_bonus(),
    }
