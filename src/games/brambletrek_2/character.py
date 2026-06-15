"""Brambletrek 2 character sheet."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.games.brambletrek_2.hollow import hollow_state_from_dict, hollow_state_to_dict

STAT_MAX = 30
STAT_MIN = 0


def get_legacy_options() -> dict[str, dict[str, str]]:
    from src.games.brambletrek_2.curated import legacy_options

    return legacy_options()


@dataclass
class Brambletrek2Character:
    id: str = ""
    name: str = ""
    legacy: str = ""
    health: int = 10
    morale: int = 10
    supplies: int = 10
    exploration_day: int = 1
    how_did_i_get_here: str = ""
    how_did_i_get_here_card: str = ""
    in_hollow: bool = False
    memory_fragments: int = 0
    hollow_awareness: bool = False
    hollow_clubs_seen: int = 0
    notes: str = ""
    legacy_abilities_used: dict[str, bool] = field(default_factory=dict)
    hollow_state: Any = None

    def is_set(self) -> bool:
        return bool(
            self.name.strip()
            or self.legacy
            or self.how_did_i_get_here
            or self.notes.strip()
            or any(v != 10 for v in (self.health, self.morale, self.supplies))
            or self.exploration_day > 1
            or self.in_hollow
            or self.memory_fragments > 0
        )

    def clamp_stats(self) -> None:
        self.health = max(STAT_MIN, min(STAT_MAX, int(self.health)))
        self.morale = max(STAT_MIN, min(STAT_MAX, int(self.morale)))
        self.supplies = max(STAT_MIN, min(STAT_MAX, int(self.supplies)))
        self.exploration_day = max(1, int(self.exploration_day))
        self.memory_fragments = max(0, int(self.memory_fragments))
        if self.memory_fragments >= 3:
            self.hollow_awareness = True

    def apply_legacy_stats(self) -> None:
        """Set resources from curated legacy spread when legacy is chosen."""
        if not self.legacy:
            return
        from src.games.brambletrek_2.curated import legacy_meta

        meta = legacy_meta(self.legacy)
        if not meta:
            return
        self.health = int(meta.get("health", self.health))
        self.morale = int(meta.get("morale", self.morale))
        self.supplies = int(meta.get("supplies", self.supplies))
        self.clamp_stats()


def arrival_band(rank_key: str) -> str:
    if rank_key == "ace":
        return "ace"
    if rank_key in ("jack", "queen", "king"):
        return rank_key
    n = int(rank_key)
    if 2 <= n <= 4:
        return "2-4"
    if 5 <= n <= 7:
        return "5-7"
    return "8-10"


def default_character() -> Brambletrek2Character:
    return Brambletrek2Character()


def character_from_dict(data: dict | None) -> Brambletrek2Character:
    if not data:
        return default_character()
    hollow_raw = data.get("hollow_state")
    return Brambletrek2Character(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        legacy=str(data.get("legacy", "") or ""),
        health=int(data.get("health", 10) or 10),
        morale=int(data.get("morale", 10) or 10),
        supplies=int(data.get("supplies", 10) or 10),
        exploration_day=int(data.get("exploration_day", 1) or 1),
        how_did_i_get_here=str(data.get("how_did_i_get_here", "") or ""),
        how_did_i_get_here_card=str(data.get("how_did_i_get_here_card", "") or ""),
        in_hollow=bool(data.get("in_hollow", False)),
        memory_fragments=int(data.get("memory_fragments", 0) or 0),
        hollow_awareness=bool(data.get("hollow_awareness", False)),
        hollow_clubs_seen=int(data.get("hollow_clubs_seen", 0) or 0),
        notes=str(data.get("notes", "") or ""),
        legacy_abilities_used={
            str(k): bool(v) for k, v in (data.get("legacy_abilities_used") or {}).items()
        },
        hollow_state=hollow_state_from_dict(hollow_raw) if hollow_raw else None,
    )


def character_to_dict(char: Brambletrek2Character) -> dict:
    char.clamp_stats()
    return {
        "id": char.id,
        "name": char.name,
        "legacy": char.legacy,
        "health": char.health,
        "morale": char.morale,
        "supplies": char.supplies,
        "exploration_day": char.exploration_day,
        "how_did_i_get_here": char.how_did_i_get_here,
        "how_did_i_get_here_card": char.how_did_i_get_here_card,
        "in_hollow": char.in_hollow,
        "memory_fragments": char.memory_fragments,
        "hollow_awareness": char.hollow_awareness,
        "hollow_clubs_seen": char.hollow_clubs_seen,
        "notes": char.notes,
        "legacy_abilities_used": dict(char.legacy_abilities_used),
        "hollow_state": hollow_state_to_dict(char.hollow_state),
    }


def save_character(char: Brambletrek2Character) -> None:
    from src.games.brambletrek_2.play import get_brambletrek_2_store

    if not char.id:
        char.id = get_brambletrek_2_store().roster.get_active_slot_id() or ""
    if char.id:
        get_brambletrek_2_store().save_entity(char)


def format_summary(char: Brambletrek2Character | None) -> str:
    if char is None or not char.is_set():
        return ""
    char.clamp_stats()
    name = char.name.strip() or "Traveller"
    legacy = get_legacy_options().get(char.legacy, {}).get("label", "")
    bits = [
        name,
        f"Day {char.exploration_day}",
        f"❤ {char.health}",
        f"☺ {char.morale}",
        f"🎒 {char.supplies}",
    ]
    if legacy:
        bits.insert(1, legacy)
    if char.in_hollow:
        bits.append(f"🌫 Hollow ({char.memory_fragments}/3 fragments)")
    return " · ".join(bits)


def format_for_prompt(
    char: Brambletrek2Character | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if char is None or not char.is_set():
        return ""
    char.clamp_stats()
    lines = ["Current Brambletrek 2 character:"]
    if char.name.strip():
        lines.append(f"- Name: {char.name.strip()}")
    if char.legacy:
        from src.games.brambletrek_2.curated import legacy_abilities, overcome_the_odds

        leg = get_legacy_options().get(char.legacy, {})
        lines.append(f"- Legacy: {leg.get('label', char.legacy)}")
        used = char.legacy_abilities_used or {}
        for ab in legacy_abilities(char.legacy):
            status = "used" if used.get(ab["id"]) else "available"
            lines.append(f"  - {ab.get('label', ab['id'])}: {status}")
        oto = overcome_the_odds()
        oto_status = "used" if used.get(oto["id"]) else "available"
        lines.append(f"  - {oto['label']}: {oto_status}")
    if char.how_did_i_get_here:
        lines.append(f"- How I got here: {char.how_did_i_get_here}")
    lines.append(
        f"- Resources: Health {char.health}, Morale {char.morale}, "
        f"Supplies {char.supplies} (each 0–{STAT_MAX})"
    )
    lines.append(f"- Exploration day: {char.exploration_day}")
    if char.in_hollow:
        lines.append(
            f"- In Misty Hollow: {char.memory_fragments} memory fragments"
            + ("; awareness gained" if char.hollow_awareness else "")
        )
    if char.notes.strip():
        lines.append(f"- Notes: {char.notes.strip()}")
    lines.append(f"- Story mode: {story_mode}")
    lines.append(f"- Card source: {card_source}")
    if char.id:
        from src.games.brambletrek_2.play import get_brambletrek_2_store

        tail = get_brambletrek_2_store().recent_log_context(char.id)
        if tail:
            lines.append("")
            lines.append(tail)
    return "\n".join(lines)
