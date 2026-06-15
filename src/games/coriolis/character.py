"""Coriolis: The Great Dark Explorer entity for solo play."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.games.coriolis.curated import (
    crew_role_options,
    profession_by_id,
    profession_options,
    talent_options,
)

_DEFAULT_ATTRIBUTES = {
    "strength": 4,
    "agility": 4,
    "logic": 4,
    "perception": 4,
    "insight": 4,
    "empathy": 4,
}

_ATTRIBUTE_BUDGET = 24
_ATTRIBUTE_MIN = 2
_ATTRIBUTE_MAX = 5
_ATTRIBUTE_KEY_MAX = 6


@dataclass
class CoriolisExplorer:
    id: str = ""
    name: str = ""
    attributes: dict[str, int] = field(default_factory=lambda: dict(_DEFAULT_ATTRIBUTES))
    profession: str = ""
    specialty: str = ""
    origin: str = ""
    talents: dict[str, int] = field(default_factory=dict)
    health: int = 0
    hope: int = 0
    heart: int = 0
    crew_name: str = ""
    bird_name: str = ""
    shuttle_name: str = ""
    rover_name: str = ""
    gear_bonus: int = 0
    last_attribute: str = "perception"
    last_talent: str = ""
    last_roll_summary: str = ""

    def max_health(self) -> int:
        return int(self.attributes.get("strength", 4) or 4) + int(
            self.attributes.get("agility", 4) or 4
        )

    def max_hope(self) -> int:
        return int(self.attributes.get("logic", 4) or 4) + int(
            self.attributes.get("empathy", 4) or 4
        )

    def max_heart(self) -> int:
        return int(self.attributes.get("insight", 4) or 4) + int(
            self.attributes.get("perception", 4) or 4
        )

    def _attribute_cap(self, key: str) -> int:
        prof = profession_by_id(self.profession)
        key_attr = str(prof.get("key_attribute", "") or "") if prof else ""
        if key_attr and key == key_attr:
            return _ATTRIBUTE_KEY_MAX
        return _ATTRIBUTE_MAX

    def clamp(self) -> None:
        self.name = str(self.name or "").strip()
        self.profession = str(self.profession or "").strip()
        self.specialty = str(self.specialty or "").strip()
        self.origin = str(self.origin or "").strip()
        self.crew_name = str(self.crew_name or "").strip()
        self.bird_name = str(self.bird_name or "").strip()
        self.shuttle_name = str(self.shuttle_name or "").strip()
        self.rover_name = str(self.rover_name or "").strip()
        self.gear_bonus = max(0, min(6, int(self.gear_bonus or 0)))
        self.last_attribute = str(self.last_attribute or "perception").strip() or "perception"
        self.last_talent = str(self.last_talent or "").strip()
        self.last_roll_summary = str(self.last_roll_summary or "")

        if not isinstance(self.attributes, dict):
            self.attributes = dict(_DEFAULT_ATTRIBUTES)
        for key in _DEFAULT_ATTRIBUTES:
            cap = self._attribute_cap(key)
            val = int(self.attributes.get(key, _DEFAULT_ATTRIBUTES[key]) or _DEFAULT_ATTRIBUTES[key])
            self.attributes[key] = max(_ATTRIBUTE_MIN, min(cap, val))

        if not isinstance(self.talents, dict):
            self.talents = {}
        cleaned: dict[str, int] = {}
        for key, val in self.talents.items():
            tid = str(key or "").strip()
            if not tid:
                continue
            cleaned[tid] = max(0, min(3, int(val or 0)))
        self.talents = cleaned

        if self.health <= 0:
            self.health = self.max_health()
        else:
            self.health = max(0, min(self.max_health(), int(self.health)))
        if self.hope <= 0:
            self.hope = self.max_hope()
        else:
            self.hope = max(0, min(self.max_hope(), int(self.hope)))
        if self.heart <= 0:
            self.heart = self.max_heart()
        else:
            self.heart = max(0, min(self.max_heart(), int(self.heart)))

    def header_fields(self) -> dict[str, Any]:
        return {
            "crew_name": self.crew_name,
            "bird_name": self.bird_name,
            "shuttle_name": self.shuttle_name,
            "rover_name": self.rover_name,
            "health": self.health,
            "max_health": self.max_health(),
            "hope": self.hope,
            "max_hope": self.max_hope(),
            "heart": self.heart,
            "max_heart": self.max_heart(),
            "profession": self.profession,
        }

    def roll_pool(self, attribute: str, talent: str = "") -> int:
        self.clamp()
        attr_key = attribute if attribute in _DEFAULT_ATTRIBUTES else self.last_attribute
        if attr_key not in self.attributes:
            attr_key = "perception"
        attr_val = int(self.attributes.get(attr_key, 4) or 4)
        talent_level = int(self.talents.get(talent, 0) or 0) if talent else 0
        return max(1, attr_val + talent_level)

    def attribute_budget_used(self) -> int:
        return sum(int(self.attributes.get(k, 0) or 0) for k in _DEFAULT_ATTRIBUTES)

    def attribute_budget_remaining(self) -> int:
        return _ATTRIBUTE_BUDGET - self.attribute_budget_used()


# Backward-compatible alias used by play registration
CoriolisCrew = CoriolisExplorer


def default_explorer() -> CoriolisExplorer:
    explorer = CoriolisExplorer()
    explorer.clamp()
    return explorer


def default_crew() -> CoriolisExplorer:
    return default_explorer()


def explorer_from_dict(data: dict[str, Any] | None) -> CoriolisExplorer:
    if not data:
        return default_explorer()
    attrs = data.get("attributes") or {}
    talents = data.get("talents") or {}
    explorer = CoriolisExplorer(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        attributes=dict(attrs) if isinstance(attrs, dict) else dict(_DEFAULT_ATTRIBUTES),
        profession=str(data.get("profession", "") or ""),
        specialty=str(data.get("specialty", "") or ""),
        origin=str(data.get("origin", "") or ""),
        talents=dict(talents) if isinstance(talents, dict) else {},
        health=int(data.get("health", 0) or 0),
        hope=int(data.get("hope", 0) or 0),
        heart=int(data.get("heart", 0) or 0),
        crew_name=str(data.get("crew_name", "") or ""),
        bird_name=str(data.get("bird_name", "") or ""),
        shuttle_name=str(data.get("shuttle_name", "") or ""),
        rover_name=str(data.get("rover_name", "") or ""),
        gear_bonus=int(data.get("gear_bonus", 0) or 0),
        last_attribute=str(data.get("last_attribute", "perception") or "perception"),
        last_talent=str(data.get("last_talent", "") or ""),
        last_roll_summary=str(data.get("last_roll_summary", "") or ""),
    )
    explorer.clamp()
    return explorer


def crew_from_dict(data: dict[str, Any] | None) -> CoriolisExplorer:
    return explorer_from_dict(data)


def explorer_to_dict(explorer: CoriolisExplorer) -> dict[str, Any]:
    explorer.clamp()
    return {
        "id": explorer.id,
        "name": explorer.name,
        "attributes": dict(explorer.attributes),
        "profession": explorer.profession,
        "specialty": explorer.specialty,
        "origin": explorer.origin,
        "talents": dict(explorer.talents),
        "health": explorer.health,
        "hope": explorer.hope,
        "heart": explorer.heart,
        "crew_name": explorer.crew_name,
        "bird_name": explorer.bird_name,
        "shuttle_name": explorer.shuttle_name,
        "rover_name": explorer.rover_name,
        "gear_bonus": explorer.gear_bonus,
        "last_attribute": explorer.last_attribute,
        "last_talent": explorer.last_talent,
        "last_roll_summary": explorer.last_roll_summary,
    }


def crew_to_dict(explorer: CoriolisExplorer) -> dict[str, Any]:
    return explorer_to_dict(explorer)


def format_summary(explorer: CoriolisExplorer) -> str:
    parts = [explorer.name or explorer.crew_name or "Explorer"]
    if explorer.bird_name:
        parts.append(explorer.bird_name)
    parts.append(f"HP {explorer.health}/{explorer.max_health()}")
    parts.append(f"Hope {explorer.hope}/{explorer.max_hope()}")
    return " · ".join(parts)


def format_for_prompt(
    explorer: CoriolisExplorer | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not explorer:
        return ""
    _ = card_source
    lines = [
        "Current Coriolis: The Great Dark solo Explorer:",
        f"- Explorer: {explorer.name or 'unnamed'}",
        f"- Profession: {explorer.profession or '(not set)'}",
        f"- Crew: {explorer.crew_name or '(not set)'}",
        f"- Bird: {explorer.bird_name or '(not set)'}",
        f"- Health/Hope/Heart: {explorer.health}/{explorer.max_health()}, "
        f"{explorer.hope}/{explorer.max_hope()}, {explorer.heart}/{explorer.max_heart()}",
        f"- Story mode: {story_mode}",
        "- Attributes: "
        + ", ".join(f"{k} {v}" for k, v in sorted(explorer.attributes.items())),
    ]
    ranked = [(k, v) for k, v in explorer.talents.items() if v > 0]
    if ranked:
        lines.append(
            "- Talents: "
            + ", ".join(f"{k} {v}" for k, v in sorted(ranked, key=lambda x: -x[1])[:8])
        )
    return "\n".join(lines)


def attribute_options() -> list[dict[str, str]]:
    return [{"id": k, "label": k.replace("_", " ").title()} for k in _DEFAULT_ATTRIBUTES]


def character_options_payload() -> dict[str, Any]:
    return {
        "attributes": attribute_options(),
        "professions": profession_options(),
        "talents": talent_options(),
        "crew_roles": crew_role_options(),
        "attribute_budget": _ATTRIBUTE_BUDGET,
    }
