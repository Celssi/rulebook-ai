"""Ashes Scion entity (dungeon journal session state)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SCION_CLASSES = ("warrior", "ordained", "pioneer", "hallowed", "deadeyed")


@dataclass
class AshesScion:
    id: str = ""
    name: str = ""
    scion_class: str = ""
    pwr: int = 3
    int_: int = 3
    agl: int = 3
    hp: int = 16
    max_hp: int = 16
    stamina: int = 6
    max_stamina: int = 6
    level: int = 1
    ember: int = 0
    rooms_cleared: int = 0
    fate_gift: str = ""
    fate_gift_card: str = ""
    armour: str = ""
    armour_roll: int = 0
    last_room_card: str = ""
    last_room_name: str = ""
    last_room_check: str = ""
    last_suit_feature: str = ""
    last_journal_card: str = ""
    last_journal_prompt: str = ""
    last_enemy_card: str = ""
    last_enemy: str = ""
    lore_count: int = 0
    sanctuaries_visited: int = 0
    trials_completed: int = 0
    active_trials: list[dict[str, str]] = field(default_factory=list)
    starting_weapon_melee: str = ""
    starting_weapon_ranged: str = ""
    notes: str = ""

    def clamp(self) -> None:
        self.pwr = max(-4, min(6, int(self.pwr)))
        self.int_ = max(-4, min(6, int(self.int_)))
        self.agl = max(-4, min(6, int(self.agl)))
        self.level = max(1, int(self.level))
        self.ember = max(0, int(self.ember))
        self.rooms_cleared = max(0, int(self.rooms_cleared))
        self.lore_count = max(0, int(self.lore_count))
        self.sanctuaries_visited = max(0, int(self.sanctuaries_visited))
        self.trials_completed = max(0, int(self.trials_completed))
        if len(self.active_trials) > 10:
            self.active_trials = self.active_trials[:10]
        self.max_hp = max(1, int(self.max_hp))
        self.hp = max(0, min(self.max_hp, int(self.hp)))
        self.max_stamina = max(1, int(self.max_stamina))
        self.stamina = max(0, min(self.max_stamina, int(self.stamina)))
        if self.scion_class and self.scion_class not in SCION_CLASSES:
            self.scion_class = ""

    def check_target(self, stat: str) -> int:
        value = {"pwr": self.pwr, "int": self.int_, "agl": self.agl}.get(stat.lower(), 0)
        return 18 - value

    def recompute_max_hp(self) -> None:
        self.max_hp = 10 + (2 * self.pwr)
        self.hp = min(self.hp, self.max_hp)

    def recompute_max_stamina(self) -> None:
        self.max_stamina = 3 + (2 * self.agl)
        self.stamina = min(self.stamina, self.max_stamina)


def default_scion() -> AshesScion:
    s = AshesScion()
    s.recompute_max_hp()
    s.recompute_max_stamina()
    return s


def scion_from_dict(data: dict | None) -> AshesScion:
    if not data:
        return default_scion()
    scion = AshesScion(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        scion_class=str(data.get("scion_class", "") or ""),
        pwr=int(data.get("pwr", 3) or 3),
        int_=int(data.get("int", data.get("int_", 3)) or 3),
        agl=int(data.get("agl", 3) or 3),
        hp=int(data.get("hp", 16) or 16),
        max_hp=int(data.get("max_hp", 16) or 16),
        stamina=int(data.get("stamina", 6) or 6),
        max_stamina=int(data.get("max_stamina", 6) or 6),
        level=int(data.get("level", 1) or 1),
        ember=int(data.get("ember", 0) or 0),
        rooms_cleared=int(data.get("rooms_cleared", 0) or 0),
        fate_gift=str(data.get("fate_gift", "") or ""),
        fate_gift_card=str(data.get("fate_gift_card", "") or ""),
        armour=str(data.get("armour", "") or ""),
        armour_roll=int(data.get("armour_roll", 0) or 0),
        last_room_card=str(data.get("last_room_card", "") or ""),
        last_room_name=str(data.get("last_room_name", "") or ""),
        last_room_check=str(data.get("last_room_check", "") or ""),
        last_suit_feature=str(data.get("last_suit_feature", "") or ""),
        last_journal_card=str(data.get("last_journal_card", "") or ""),
        last_journal_prompt=str(data.get("last_journal_prompt", "") or ""),
        last_enemy_card=str(data.get("last_enemy_card", "") or ""),
        last_enemy=str(data.get("last_enemy", "") or ""),
        lore_count=int(data.get("lore_count", 0) or 0),
        sanctuaries_visited=int(data.get("sanctuaries_visited", 0) or 0),
        trials_completed=int(data.get("trials_completed", 0) or 0),
        active_trials=list(data.get("active_trials") or []),
        starting_weapon_melee=str(data.get("starting_weapon_melee", "") or ""),
        starting_weapon_ranged=str(data.get("starting_weapon_ranged", "") or ""),
        notes=str(data.get("notes", "") or ""),
    )
    scion.clamp()
    return scion


def scion_to_dict(scion: AshesScion) -> dict[str, Any]:
    scion.clamp()
    return {
        "id": scion.id,
        "name": scion.name,
        "scion_class": scion.scion_class,
        "pwr": scion.pwr,
        "int": scion.int_,
        "agl": scion.agl,
        "hp": scion.hp,
        "max_hp": scion.max_hp,
        "stamina": scion.stamina,
        "max_stamina": scion.max_stamina,
        "level": scion.level,
        "ember": scion.ember,
        "rooms_cleared": scion.rooms_cleared,
        "fate_gift": scion.fate_gift,
        "fate_gift_card": scion.fate_gift_card,
        "armour": scion.armour,
        "armour_roll": scion.armour_roll,
        "last_room_card": scion.last_room_card,
        "last_room_name": scion.last_room_name,
        "last_room_check": scion.last_room_check,
        "last_suit_feature": scion.last_suit_feature,
        "last_journal_card": scion.last_journal_card,
        "last_journal_prompt": scion.last_journal_prompt,
        "last_enemy_card": scion.last_enemy_card,
        "last_enemy": scion.last_enemy,
        "lore_count": scion.lore_count,
        "sanctuaries_visited": scion.sanctuaries_visited,
        "trials_completed": scion.trials_completed,
        "active_trials": list(scion.active_trials),
        "starting_weapon_melee": scion.starting_weapon_melee,
        "starting_weapon_ranged": scion.starting_weapon_ranged,
        "notes": scion.notes,
    }


def format_summary(scion: AshesScion) -> str:
    parts = [scion.name.strip() or "Scion"]
    if scion.scion_class:
        parts.append(scion.scion_class.title())
    parts.append(f"Lv {scion.level}")
    parts.append(f"HP {scion.hp}/{scion.max_hp}")
    if scion.rooms_cleared:
        parts.append(f"{scion.rooms_cleared} rooms")
    if scion.ember:
        parts.append(f"Ember {scion.ember}")
    return " · ".join(parts)


def format_for_prompt(
    scion: AshesScion | None,
    *,
    card_source: str = "virtual",
    story_mode: str = "player",
) -> str:
    if not scion or not scion.name.strip():
        return ""
    lines = [
        f"Scion: {scion.name}",
        f"Class: {scion.scion_class or 'unset'}",
        f"Stats PWR/INT/AGL: {scion.pwr}/{scion.int_}/{scion.agl} "
        f"(checks {scion.check_target('pwr')}/{scion.check_target('int')}/{scion.check_target('agl')})",
        f"HP {scion.hp}/{scion.max_hp}, Stamina {scion.stamina}/{scion.max_stamina}",
        f"Level {scion.level}, Ember {scion.ember}, Rooms cleared {scion.rooms_cleared}, Lore {scion.lore_count}",
    ]
    if scion.active_trials:
        lines.append(f"Active trials ({len(scion.active_trials)}): " + "; ".join(
            t.get("trial", "")[:60] for t in scion.active_trials[:3]
        ))
    if scion.fate_gift:
        lines.append(f"Fate's Gift: {scion.fate_gift}")
    if scion.armour:
        lines.append(f"Armour: {scion.armour}")
    if scion.last_room_name:
        lines.append(f"Last room: {scion.last_room_name} ({scion.last_room_card})")
    if scion.last_journal_prompt:
        lines.append(f"Last journal prompt: {scion.last_journal_prompt[:120]}")
    lines.append(f"Story mode: {story_mode}; card source: {card_source}")
    return "\n".join(lines)
