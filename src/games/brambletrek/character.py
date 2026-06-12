"""Brambletrek Gnawborn character sheet (stats + creation choices)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import yaml

from src.settings import CURATED_DIR

TABLES_YAML = CURATED_DIR / "brambletrek_character_tables.yaml"

STAT_MAX = 20
STAT_MIN = 0

def get_legacy_options() -> dict[str, dict[str, str]]:
    from src.games.brambletrek.curated import legacy_options

    return legacy_options()


@dataclass
class BrambletrekCharacter:
    id: str = ""
    name: str = ""
    reason_band: str = ""
    background_band: str = ""
    trinket_band: str = ""
    legacy: str = ""
    health: int = 10
    morale: int = 10
    supplies: int = 10
    journey_day: int = 1
    in_aldwund: bool = False
    active_adventure: str = ""
    reason_card: str = ""
    background_card: str = ""
    trinket_card: str = ""
    notes: str = ""
    legacy_abilities_used: dict[str, bool] = field(default_factory=dict)

    def is_set(self) -> bool:
        return bool(
            self.name.strip()
            or self.reason_band
            or self.background_band
            or self.trinket_band
            or self.legacy
            or self.notes.strip()
            or any(v != 10 for v in (self.health, self.morale, self.supplies))
            or self.journey_day > 1
        )

    def clamp_stats(self) -> None:
        self.health = max(STAT_MIN, min(STAT_MAX, int(self.health)))
        self.morale = max(STAT_MIN, min(STAT_MAX, int(self.morale)))
        self.supplies = max(STAT_MIN, min(STAT_MAX, int(self.supplies)))
        self.journey_day = max(1, int(self.journey_day))


_tables_cache: dict[str, Any] | None = None


def load_character_tables() -> dict[str, Any]:
    global _tables_cache
    if _tables_cache is None:
        if not TABLES_YAML.exists():
            _tables_cache = {"reasons": {}, "backgrounds": {}, "trinkets": {}, "card_bands": []}
        else:
            _tables_cache = yaml.safe_load(TABLES_YAML.read_text(encoding="utf-8")) or {}
    return _tables_cache


def table_options(table_key: str) -> list[tuple[str, str]]:
    """Return (id, label) pairs for select boxes."""
    data = load_character_tables()
    rows = data.get(table_key, {}) or {}
    options: list[tuple[str, str]] = [("", "— Not set —")]
    for band_id, meta in rows.items():
        if isinstance(meta, dict):
            options.append((str(band_id), meta.get("label", str(band_id))))
    return options


def label_for_band(table_key: str, band_id: str) -> str:
    if not band_id:
        return ""
    data = load_character_tables()
    row = (data.get(table_key) or {}).get(band_id)
    if isinstance(row, dict):
        return row.get("label", band_id)
    return band_id


def default_character() -> BrambletrekCharacter:
    return BrambletrekCharacter()


def character_from_dict(data: dict | None) -> BrambletrekCharacter:
    if not data:
        return default_character()
    return BrambletrekCharacter(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        reason_band=str(data.get("reason_band", "") or ""),
        background_band=str(data.get("background_band", "") or ""),
        trinket_band=str(data.get("trinket_band", "") or ""),
        legacy=str(data.get("legacy", "") or ""),
        health=int(data.get("health", 10) or 10),
        morale=int(data.get("morale", 10) or 10),
        supplies=int(data.get("supplies", 10) or 10),
        journey_day=int(data.get("journey_day", 1) or 1),
        in_aldwund=bool(data.get("in_aldwund", False)),
        active_adventure=str(data.get("active_adventure", "") or ""),
        reason_card=str(data.get("reason_card", "") or ""),
        background_card=str(data.get("background_card", "") or ""),
        trinket_card=str(data.get("trinket_card", "") or ""),
        notes=str(data.get("notes", "") or ""),
        legacy_abilities_used={
            str(k): bool(v)
            for k, v in (data.get("legacy_abilities_used") or {}).items()
        },
    )


def character_to_dict(char: BrambletrekCharacter) -> dict:
    char.clamp_stats()
    return {
        "id": char.id,
        "name": char.name,
        "reason_band": char.reason_band,
        "background_band": char.background_band,
        "trinket_band": char.trinket_band,
        "legacy": char.legacy,
        "health": char.health,
        "morale": char.morale,
        "supplies": char.supplies,
        "journey_day": char.journey_day,
        "in_aldwund": char.in_aldwund,
        "active_adventure": char.active_adventure,
        "reason_card": char.reason_card,
        "background_card": char.background_card,
        "trinket_card": char.trinket_card,
        "notes": char.notes,
        "legacy_abilities_used": dict(char.legacy_abilities_used),
    }


def save_character(char: BrambletrekCharacter) -> None:
    """Save character via play roster (requires char.id)."""
    from src.games.brambletrek.play import get_brambletrek_store

    if not char.id:
        char.id = get_brambletrek_store().roster.get_active_slot_id() or ""
    if char.id:
        get_brambletrek_store().save_entity(char)


def format_summary(char: BrambletrekCharacter | None) -> str:
    if char is None or not char.is_set():
        return ""
    char.clamp_stats()
    name = char.name.strip() or "Gnawborn"
    legacy = get_legacy_options().get(char.legacy, {}).get("label", "")
    bits = [
        name,
        f"Day {char.journey_day}",
        f"❤ {char.health}",
        f"☺ {char.morale}",
        f"🎒 {char.supplies}",
    ]
    if legacy and legacy != "— Not set —":
        bits.insert(1, legacy)
    return " · ".join(bits)


def format_for_prompt(
    char: BrambletrekCharacter | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if char is None or not char.is_set():
        return ""
    char.clamp_stats()
    lines = ["Current Gnawborn character (use for journey/combat/recovery answers):"]
    if char.name.strip():
        lines.append(f"- Name: {char.name.strip()}")
    if char.reason_band:
        lines.append(f"- Reason: {label_for_band('reasons', char.reason_band)}")
    if char.reason_card:
        lines.append(f"- Reason card drawn: {char.reason_card}")
    if char.background_band:
        lines.append(f"- Background: {label_for_band('backgrounds', char.background_band)}")
    if char.background_card:
        lines.append(f"- Background card drawn: {char.background_card}")
    if char.trinket_band:
        lines.append(f"- Trinket: {label_for_band('trinkets', char.trinket_band)}")
    if char.trinket_card:
        lines.append(f"- Trinket card drawn: {char.trinket_card}")
    if char.legacy:
        from src.games.brambletrek.curated import legacy_abilities, overcome_the_odds

        leg = get_legacy_options().get(char.legacy, {})
        lines.append(
            f"- Legacy: {leg.get('label', char.legacy)} "
            f"(boost {leg.get('boost', '?')}, flaw {leg.get('flaw', '?')})"
        )
        used = char.legacy_abilities_used or {}
        for ab in legacy_abilities(char.legacy):
            status = "used" if used.get(ab["id"]) else "available"
            lines.append(f"  - {ab.get('label', ab['id'])}: {status}")
        oto = overcome_the_odds()
        oto_status = "used" if used.get(oto["id"]) else "available"
        lines.append(f"  - {oto['label']}: {oto_status}")
    lines.append(
        f"- Resources: Health {char.health}, Morale {char.morale}, "
        f"Supplies {char.supplies} (each 0–{STAT_MAX}; at 0 roll recovery table)"
    )
    lines.append(f"- Journey day: {char.journey_day}")
    if char.in_aldwund:
        lines.append("- Location: Aldwund (Depths) — use depths journey table (pp. 26–27)")
    if char.active_adventure:
        from src.games.brambletrek.curated import adventure_meta

        adv = adventure_meta(char.active_adventure)
        lines.append(
            f"- Active adventure: {adv.get('label', char.active_adventure)} "
            f"(prefer this module's PDF when answering scene questions)"
        )
    if char.notes.strip():
        lines.append(f"- Notes: {char.notes.strip()}")
    lines.append(f"- Story mode: {story_mode} (player = facilitator only; ai_narrator = add narrative)")
    lines.append(f"- Card source: {card_source} (physical = user reports cards; virtual = app draws)")
    if char.id:
        from src.games.brambletrek.play import get_brambletrek_store

        tail = get_brambletrek_store().recent_log_context(char.id)
        if tail:
            lines.append("")
            lines.append(tail)
    lines.append(
        "When suggesting stat changes from events, apply them to these current values."
    )
    return "\n".join(lines)
