"""MLP pony entity (level 1 character sheet)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.games.mlp.curated import (
    ESSENCE_KEYS,
    compute_defenses,
    ladder_ids,
    origin_derived,
    options_payload,
    rank_to_ladder_index,
    recompute_essences,
    validate_level1_character,
)


def _default_base_essences() -> dict[str, int]:
    return {k: 3 for k in ESSENCE_KEYS}


def _default_skills() -> dict[str, int]:
    return {}


@dataclass
class MlpPony:
    id: str = ""
    name: str = ""
    pony_name: str = ""
    origin: str = ""
    role: str = ""
    influences: list[str] = field(default_factory=list)
    hang_ups: list[str] = field(default_factory=list)
    background_bonds: list[str] = field(default_factory=list)
    cutie_mark: str = ""
    cutie_mark_perk_skill: str = ""
    base_essences: dict[str, int] = field(default_factory=_default_base_essences)
    origin_essence_target: str = ""
    essences: dict[str, int] = field(default_factory=_default_base_essences)
    defenses: dict[str, int] = field(default_factory=dict)
    skills: dict[str, int] = field(default_factory=_default_skills)
    spellcasting_rank: int = 0
    spellcasting_current: int = -1
    spell_cost: int = 1
    default_dif: int = 15
    default_skill_id: str = "alertness"
    edge_snag: str = "normal"
    friendship_points: int = 1
    health: int = 2
    movement: int = 30
    last_roll_summary: str = ""

    def clamp(self) -> None:
        self.name = str(self.name or "").strip()
        self.pony_name = str(self.pony_name or self.name or "").strip()
        if not self.name and self.pony_name:
            self.name = self.pony_name
        self.origin = str(self.origin or "").strip()
        self.role = str(self.role or "").strip()
        self.cutie_mark = str(self.cutie_mark or "").strip()
        self.cutie_mark_perk_skill = str(self.cutie_mark_perk_skill or "").strip()
        self.origin_essence_target = str(self.origin_essence_target or "").strip()
        self.default_skill_id = str(self.default_skill_id or "alertness").strip()
        self.edge_snag = str(self.edge_snag or "normal").strip()
        if self.edge_snag not in ("normal", "edge", "snag"):
            self.edge_snag = "normal"

        if not isinstance(self.influences, list):
            self.influences = []
        self.influences = [str(x).strip() for x in self.influences if str(x).strip()][:3]

        if not isinstance(self.hang_ups, list):
            self.hang_ups = []
        self.hang_ups = [str(x).strip() for x in self.hang_ups if str(x).strip()][:2]

        if not isinstance(self.background_bonds, list):
            self.background_bonds = []
        self.background_bonds = [str(x).strip() for x in self.background_bonds if str(x).strip()][:3]

        if not isinstance(self.base_essences, dict):
            self.base_essences = _default_base_essences()
        self.base_essences = {
            k: max(1, min(10, int(self.base_essences.get(k, 3) or 3))) for k in ESSENCE_KEYS
        }

        if not isinstance(self.skills, dict):
            self.skills = {}
        self.skills = {str(k): max(0, min(6, int(v or 0))) for k, v in self.skills.items()}

        self.spellcasting_rank = max(0, min(6, int(self.spellcasting_rank or 0)))
        max_ladder = len(ladder_ids()) - 1
        if self.spellcasting_current < 0:
            self.spellcasting_current = rank_to_ladder_index(self.spellcasting_rank) if self.spellcasting_rank else 0
        self.spellcasting_current = max(0, min(max_ladder, int(self.spellcasting_current)))
        self.spell_cost = max(1, min(6, int(self.spell_cost or 1)))
        self.default_dif = max(5, min(40, int(self.default_dif or 15)))
        self.friendship_points = max(0, min(20, int(self.friendship_points or 1)))
        self.health = max(1, min(30, int(self.health or 2)))
        self.movement = max(5, min(100, int(self.movement or 30)))
        self.last_roll_summary = str(self.last_roll_summary or "").strip()

        self.recompute_derived()

    def recompute_derived(self) -> None:
        self.essences = recompute_essences(
            self.base_essences,
            origin=self.origin,
            origin_essence_target=self.origin_essence_target,
            role=self.role,
        )
        self.defenses = compute_defenses(self.essences)
        if self.origin:
            derived = origin_derived(self.origin)
            self.health = derived["health"]
            self.movement = derived["movement"]
            if self.spellcasting_rank == 0 and derived.get("default_spellcasting_rank"):
                self.spellcasting_rank = int(derived["default_spellcasting_rank"])
        if self.spellcasting_rank > 0:
            total_idx = rank_to_ladder_index(self.spellcasting_rank)
            if self.spellcasting_current < 0:
                self.spellcasting_current = total_idx
        else:
            self.spellcasting_current = 0

    def header_fields(self) -> dict[str, Any]:
        return {
            "pony_name": self.pony_name,
            "origin": self.origin,
            "role": self.role,
            "friendship_points": self.friendship_points,
            "spellcasting_rank": self.spellcasting_rank,
            "spellcasting_current": self.spellcasting_current,
        }


def default_pony() -> MlpPony:
    pony = MlpPony()
    pony.clamp()
    return pony


def _migrate_legacy(data: dict[str, Any]) -> dict[str, Any]:
    out = dict(data)
    if not out.get("origin") and out.get("pony_type"):
        origin = str(out["pony_type"])
        if origin == "alicorn":
            origin = "unicorn"
        out["origin"] = origin
    if not out.get("background_bonds") and out.get("quirk"):
        out["background_bonds"] = [str(out["quirk"])]
    if not out.get("cutie_mark") and out.get("talent"):
        out["cutie_mark"] = str(out["talent"])
    if "magic_shift" in out:
        out.pop("magic_shift", None)
    if not out.get("base_essences") and not out.get("essences"):
        out["base_essences"] = _default_base_essences()
    elif not out.get("base_essences") and out.get("essences"):
        out["base_essences"] = dict(out["essences"])
    return out


def pony_from_dict(data: dict[str, Any] | None) -> MlpPony:
    if not data:
        return default_pony()
    data = _migrate_legacy(data)
    sc_rank = int(data.get("spellcasting_rank", 0) or 0)
    sc_raw = int(data.get("spellcasting_current", -1) if data.get("spellcasting_current") is not None else -1)
    if sc_rank > 0 and sc_raw < 0:
        sc_current = rank_to_ladder_index(sc_rank)
    else:
        sc_current = sc_raw if sc_raw >= 0 else 0
    pony = MlpPony(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        pony_name=str(data.get("pony_name", "") or ""),
        origin=str(data.get("origin", "") or ""),
        role=str(data.get("role", "") or ""),
        influences=list(data.get("influences") or []),
        hang_ups=list(data.get("hang_ups") or []),
        background_bonds=list(data.get("background_bonds") or []),
        cutie_mark=str(data.get("cutie_mark", "") or ""),
        cutie_mark_perk_skill=str(data.get("cutie_mark_perk_skill", "") or ""),
        base_essences=dict(data.get("base_essences") or _default_base_essences()),
        origin_essence_target=str(data.get("origin_essence_target", "") or ""),
        essences=dict(data.get("essences") or _default_base_essences()),
        defenses=dict(data.get("defenses") or {}),
        skills=dict(data.get("skills") or {}),
        spellcasting_rank=sc_rank,
        spellcasting_current=sc_current,
        spell_cost=int(data.get("spell_cost", 1) or 1),
        default_dif=int(data.get("default_dif", 15) or 15),
        default_skill_id=str(data.get("default_skill_id", "alertness") or "alertness"),
        edge_snag=str(data.get("edge_snag", "normal") or "normal"),
        friendship_points=int(data.get("friendship_points", 1) or 1),
        health=int(data.get("health", 2) or 2),
        movement=int(data.get("movement", 30) or 30),
        last_roll_summary=str(data.get("last_roll_summary", "") or ""),
    )
    pony.clamp()
    return pony


def pony_to_dict(pony: MlpPony) -> dict[str, Any]:
    pony.clamp()
    return {
        "id": pony.id,
        "name": pony.name,
        "pony_name": pony.pony_name,
        "origin": pony.origin,
        "role": pony.role,
        "influences": pony.influences,
        "hang_ups": pony.hang_ups,
        "background_bonds": pony.background_bonds,
        "cutie_mark": pony.cutie_mark,
        "cutie_mark_perk_skill": pony.cutie_mark_perk_skill,
        "base_essences": pony.base_essences,
        "origin_essence_target": pony.origin_essence_target,
        "essences": pony.essences,
        "defenses": pony.defenses,
        "skills": pony.skills,
        "spellcasting_rank": pony.spellcasting_rank,
        "spellcasting_current": pony.spellcasting_current,
        "spell_cost": pony.spell_cost,
        "default_dif": pony.default_dif,
        "default_skill_id": pony.default_skill_id,
        "edge_snag": pony.edge_snag,
        "friendship_points": pony.friendship_points,
        "health": pony.health,
        "movement": pony.movement,
        "last_roll_summary": pony.last_roll_summary,
    }


def format_summary(pony: MlpPony) -> str:
    who = pony.pony_name or pony.name or "Pony"
    parts = [who]
    if pony.origin:
        parts.append(pony.origin.replace("_", " ").title())
    if pony.role:
        parts.append(pony.role.replace("spirit_of_", "Spirit of ").replace("_", " ").title())
    ess = pony.essences
    if any(ess.values()):
        parts.append(
            "Str {strength} Spd {speed} Smt {smarts} Soc {social}".format(**{k: ess.get(k, 0) for k in ESSENCE_KEYS})
        )
    if pony.spellcasting_rank:
        parts.append(f"Spell d{['—','2','4','6','8','10','12'][pony.spellcasting_rank]}")
    return " · ".join(parts)


def format_for_prompt(
    pony: MlpPony | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not pony:
        return ""
    lines = [
        "Current MLP pony (level 1):",
        f"- Pony name: {pony.pony_name or 'unnamed'}",
        f"- Origin: {pony.origin or '(not set)'}",
        f"- Role: {pony.role or '(not set)'}",
        f"- Influences: {', '.join(pony.influences) or '(none)'}",
        f"- Hang-Ups: {', '.join(pony.hang_ups) or '(none)'}",
        f"- Cutie Mark: {pony.cutie_mark or '(not set)'}",
        f"- Essences: Str {pony.essences.get('strength', 0)}, Spd {pony.essences.get('speed', 0)}, "
        f"Smt {pony.essences.get('smarts', 0)}, Soc {pony.essences.get('social', 0)}",
        f"- Defenses: Toughness {pony.defenses.get('toughness', 0)}, Evasion {pony.defenses.get('evasion', 0)}, "
        f"Willpower {pony.defenses.get('willpower', 0)}, Cleverness {pony.defenses.get('cleverness', 0)}",
        f"- Friendship Points: {pony.friendship_points}",
        f"- Spellcasting rank: {pony.spellcasting_rank}, current ladder step: {pony.spellcasting_current}",
        f"- Story mode: {story_mode}",
        f"- Deck: {card_source}",
    ]
    return "\n".join(lines)


def pony_options_payload() -> dict[str, Any]:
    return options_payload()


def validation_errors(pony: MlpPony) -> list[str]:
    return validate_level1_character(pony_to_dict(pony))
