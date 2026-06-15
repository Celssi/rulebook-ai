"""Outgunned solo hero entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.games.outgunned.curated import (
    attribute_ids,
    lookup_role,
    lookup_trope,
    reset_tension,
    skill_ids,
)

_DEFAULT_ATTRS = ("Brawn", "Nerves", "Smooth", "Focus", "Crime")
_BASE_ATTR = 2
_BASE_SKILL = 1
_MAX_SCORE = 3
_MIN_POOL = 2
_MAX_POOL = 9


def _default_attributes() -> dict[str, int]:
    return {a: _BASE_ATTR for a in attribute_ids() or list(_DEFAULT_ATTRS)}


def _default_skills() -> dict[str, int]:
    return {s: _BASE_SKILL for s in skill_ids()}


def _clamp_score(value: int) -> int:
    return max(0, min(_MAX_SCORE, int(value or 0)))


@dataclass
class OutgunnedHero:
    id: str = ""
    name: str = ""
    mission_title: str = ""
    role: str = ""
    trope: str = ""
    age: str = "Adult"
    background: str = ""
    catchphrase: str = ""
    flaw: str = ""
    attributes: dict[str, int] = field(default_factory=_default_attributes)
    skills: dict[str, int] = field(default_factory=_default_skills)
    feats: list[str] = field(default_factory=list)
    solo_boosts_applied: bool = False
    solo_boost_attr: str = ""
    solo_boost_skills: list[str] = field(default_factory=list)
    roll_attribute: str = ""
    roll_skill: str = ""
    ad_state: dict[str, Any] = field(default_factory=dict)
    last_prompt: str = ""
    last_roll_summary: str = ""
    death_roulette_bullets: int = 1

    def clamp(self) -> None:
        self.name = str(self.name or "").strip()
        self.mission_title = str(self.mission_title or "").strip()
        self.role = str(self.role or "").strip()
        self.trope = str(self.trope or "").strip()
        self.age = str(self.age or "Adult").strip() or "Adult"
        self.background = str(self.background or "").strip()
        self.catchphrase = str(self.catchphrase or "").strip()
        self.flaw = str(self.flaw or "").strip()
        self.solo_boost_attr = str(self.solo_boost_attr or "").strip()
        self.roll_attribute = str(self.roll_attribute or "").strip()
        self.roll_skill = str(self.roll_skill or "").strip()
        self.death_roulette_bullets = max(0, min(6, int(self.death_roulette_bullets or 0)))
        if not isinstance(self.ad_state, dict):
            self.ad_state = {}
        if not isinstance(self.attributes, dict):
            self.attributes = _default_attributes()
        if not isinstance(self.skills, dict):
            self.skills = _default_skills()
        if not isinstance(self.feats, list):
            self.feats = []
        if not isinstance(self.solo_boost_skills, list):
            self.solo_boost_skills = []
        for key in attribute_ids() or list(_DEFAULT_ATTRS):
            self.attributes.setdefault(key, _BASE_ATTR)
            self.attributes[key] = _clamp_score(self.attributes.get(key, _BASE_ATTR))
        for key in skill_ids():
            self.skills.setdefault(key, _BASE_SKILL)
            self.skills[key] = _clamp_score(self.skills.get(key, _BASE_SKILL))
        tension = self.ad_state.get("tension")
        if tension is None:
            phase = str(self.ad_state.get("phase", "") or "")
            self.ad_state["tension"] = reset_tension(phase=phase)
        else:
            self.ad_state["tension"] = max(0, min(12, int(tension or 0)))

    def _bump_attr(self, attr: str) -> None:
        if attr in self.attributes:
            self.attributes[attr] = _clamp_score(self.attributes[attr] + 1)

    def _bump_skill(self, skill: str) -> None:
        if skill in self.skills:
            self.skills[skill] = _clamp_score(self.skills[skill] + 1)

    def apply_role(self, role_id: str) -> None:
        row = lookup_role(role_id)
        if not row:
            return
        self.role = str(row.get("id", role_id))
        self.attributes = _default_attributes()
        self.skills = _default_skills()
        self.feats = []
        self.solo_boosts_applied = False
        if row.get("special"):
            for attr in row.get("attribute_points") or []:
                self._bump_attr(str(attr))
        else:
            attr = str(row.get("attribute_point", "") or "")
            if attr:
                self._bump_attr(attr)
        for skill in row.get("skill_points") or []:
            self._bump_skill(str(skill))
        if row.get("special"):
            self.trope = ""

    def apply_trope(self, trope_id: str) -> None:
        if lookup_role(self.role).get("special"):
            return
        row = lookup_trope(trope_id)
        if not row:
            return
        self.trope = str(row.get("id", trope_id))
        options = [str(a) for a in row.get("attribute_options") or []]
        role_row = lookup_role(self.role)
        role_attr = str(role_row.get("attribute_point", "") or "")
        attr_pick = options[1] if len(options) > 1 and role_attr == options[0] else options[0]
        if attr_pick:
            self._bump_attr(attr_pick)
        for skill in row.get("skill_points") or []:
            self._bump_skill(str(skill))

    def apply_solo_boosts(self, *, attr: str = "", skills: list[str] | None = None) -> None:
        """AD s. 46: +1 Attribute, +2 Skill Points."""
        if self.solo_boosts_applied:
            return
        pick_attr = str(attr or self.solo_boost_attr or "").strip()
        if pick_attr:
            self._bump_attr(pick_attr)
            self.solo_boost_attr = pick_attr
        for skill in skills or self.solo_boost_skills or []:
            self._bump_skill(str(skill))
        if skills:
            self.solo_boost_skills = [str(s) for s in skills]
        self.solo_boosts_applied = True

    def pool_dice_count(self, *, attribute: str = "", skill: str = "") -> int:
        attr = str(attribute or self.roll_attribute or "").strip()
        sk = str(skill or self.roll_skill or "").strip()
        if attr and sk and attr in self.attributes and sk in self.skills:
            total = int(self.attributes[attr]) + int(self.skills[sk])
            return max(_MIN_POOL, min(_MAX_POOL, total))
        fallback = int(self.ad_state.get("pool_dice", 3) or 3)
        return max(_MIN_POOL, min(_MAX_POOL, fallback))

    def header_fields(self) -> dict[str, Any]:
        return {
            "mission_title": self.mission_title,
            "death_roulette_bullets": self.death_roulette_bullets,
            "ad_phase": str(self.ad_state.get("phase", "") or ""),
            "tension": int(self.ad_state.get("tension", 1) or 1),
            "role": self.role,
            "trope": self.trope,
        }


def default_hero() -> OutgunnedHero:
    hero = OutgunnedHero()
    hero.clamp()
    return hero


def hero_from_dict(data: dict[str, Any] | None) -> OutgunnedHero:
    if not data:
        return default_hero()
    ad = data.get("ad_state") or {}
    hero = OutgunnedHero(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        mission_title=str(data.get("mission_title", "") or ""),
        role=str(data.get("role", "") or ""),
        trope=str(data.get("trope", "") or ""),
        age=str(data.get("age", "Adult") or "Adult"),
        background=str(data.get("background", "") or ""),
        catchphrase=str(data.get("catchphrase", "") or ""),
        flaw=str(data.get("flaw", "") or ""),
        attributes=dict(data.get("attributes") or _default_attributes()),
        skills=dict(data.get("skills") or _default_skills()),
        feats=[str(f) for f in (data.get("feats") or []) if f],
        solo_boosts_applied=bool(data.get("solo_boosts_applied")),
        solo_boost_attr=str(data.get("solo_boost_attr", "") or ""),
        solo_boost_skills=[str(s) for s in (data.get("solo_boost_skills") or []) if s],
        roll_attribute=str(data.get("roll_attribute", "") or ""),
        roll_skill=str(data.get("roll_skill", "") or ""),
        ad_state=dict(ad) if isinstance(ad, dict) else {},
        last_prompt=str(data.get("last_prompt", "") or ""),
        last_roll_summary=str(data.get("last_roll_summary", "") or ""),
        death_roulette_bullets=int(data.get("death_roulette_bullets", 1) or 1),
    )
    hero.clamp()
    return hero


def hero_to_dict(hero: OutgunnedHero) -> dict[str, Any]:
    hero.clamp()
    return {
        "id": hero.id,
        "name": hero.name,
        "mission_title": hero.mission_title,
        "role": hero.role,
        "trope": hero.trope,
        "age": hero.age,
        "background": hero.background,
        "catchphrase": hero.catchphrase,
        "flaw": hero.flaw,
        "attributes": dict(hero.attributes),
        "skills": dict(hero.skills),
        "feats": list(hero.feats),
        "solo_boosts_applied": hero.solo_boosts_applied,
        "solo_boost_attr": hero.solo_boost_attr,
        "solo_boost_skills": list(hero.solo_boost_skills),
        "roll_attribute": hero.roll_attribute,
        "roll_skill": hero.roll_skill,
        "ad_state": dict(hero.ad_state),
        "last_prompt": hero.last_prompt,
        "last_roll_summary": hero.last_roll_summary,
        "death_roulette_bullets": hero.death_roulette_bullets,
    }


def character_options_payload() -> dict[str, Any]:
    from src.games.outgunned.curated import age_options, role_entries, trope_entries

    return {
        "roles": role_entries(),
        "tropes": trope_entries(),
        "attributes": attribute_ids() or list(_DEFAULT_ATTRS),
        "skills": skill_ids(),
        "ages": age_options(),
    }


def format_summary(hero: OutgunnedHero) -> str:
    parts = [hero.name or "Hero"]
    if hero.role:
        row = lookup_role(hero.role)
        parts.append(str(row.get("label", hero.role)))
    if hero.mission_title:
        parts.append(hero.mission_title)
    phase = str(hero.ad_state.get("phase", "") or "")
    if phase:
        parts.append(phase)
    tension = int(hero.ad_state.get("tension", 0) or 0)
    if tension:
        parts.append(f"Tension {tension}/12")
    if hero.death_roulette_bullets:
        parts.append(f"Roulette {hero.death_roulette_bullets}/6")
    return " · ".join(parts)


def format_for_prompt(
    hero: OutgunnedHero | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not hero:
        return ""
    lines = [
        "Current Outgunned solo hero:",
        f"- Hero: {hero.name or 'unnamed'}",
        f"- Mission: {hero.mission_title or '(not set)'}",
        f"- Story mode: {story_mode}",
    ]
    if hero.role:
        row = lookup_role(hero.role)
        lines.append(f"- Role: {row.get('label', hero.role)}")
    if hero.trope:
        row = lookup_trope(hero.trope)
        lines.append(f"- Trope: {row.get('label', hero.trope)}")
    if hero.background:
        lines.append(f"- Background: {hero.background}")
    if hero.catchphrase:
        lines.append(f"- Catchphrase: {hero.catchphrase}")
    villain = hero.ad_state.get("villain")
    if isinstance(villain, dict) and villain:
        lines.append(
            "- Villain: " + ", ".join(f"{k}={v}" for k, v in villain.items() if v)
        )
    phase = hero.ad_state.get("phase")
    if phase:
        lines.append(f"- Campaign phase: {phase}")
    tension = hero.ad_state.get("tension")
    if tension is not None:
        lines.append(f"- Tension: {tension}/12")
    aim = hero.ad_state.get("aim")
    hurdle = hero.ad_state.get("hurdle")
    if aim:
        lines.append(f"- Aim: {aim}")
    if hurdle:
        lines.append(f"- Hurdle: {hurdle}")
    if hero.roll_attribute and hero.roll_skill:
        lines.append(
            f"- Roll pool: {hero.roll_attribute}+{hero.roll_skill} "
            f"({hero.pool_dice_count()}d6)"
        )
    if hero.last_prompt:
        lines.append(f"- Last AD prompt: {hero.last_prompt[:200]}")
    return "\n".join(lines)
