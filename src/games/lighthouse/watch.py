"""Keeper watch entity for The Lighthouse at the Edge of the Universe."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class KeeperWatch:
    id: str = ""
    name: str = ""
    night_count: int = 1
    weather_mood: str = ""
    lamp_lit: bool = False
    inventory_notes: list[str] = field(default_factory=list)
    last_task: str = ""
    last_cards: list[str] = field(default_factory=list)

    def clamp(self) -> None:
        self.night_count = max(1, int(self.night_count or 1))
        self.name = str(self.name or "").strip()
        self.weather_mood = str(self.weather_mood or "").strip()
        self.last_task = str(self.last_task or "").strip()
        if not isinstance(self.inventory_notes, list):
            self.inventory_notes = []
        if not isinstance(self.last_cards, list):
            self.last_cards = []


def default_watch() -> KeeperWatch:
    return KeeperWatch()


def watch_from_dict(data: dict[str, Any] | None) -> KeeperWatch:
    if not data:
        return default_watch()
    inv = data.get("inventory_notes") or []
    cards = data.get("last_cards") or []
    return KeeperWatch(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        night_count=int(data.get("night_count", 1) or 1),
        weather_mood=str(data.get("weather_mood", "") or ""),
        lamp_lit=bool(data.get("lamp_lit", False)),
        inventory_notes=[str(x) for x in inv] if isinstance(inv, list) else [],
        last_task=str(data.get("last_task", "") or ""),
        last_cards=[str(x) for x in cards] if isinstance(cards, list) else [],
    )


def watch_to_dict(watch: KeeperWatch) -> dict[str, Any]:
    watch.clamp()
    return {
        "id": watch.id,
        "name": watch.name,
        "night_count": watch.night_count,
        "weather_mood": watch.weather_mood,
        "lamp_lit": watch.lamp_lit,
        "inventory_notes": list(watch.inventory_notes),
        "last_task": watch.last_task,
        "last_cards": list(watch.last_cards),
    }


def format_summary(watch: KeeperWatch) -> str:
    from src.games.lighthouse.curated import lookup_weather

    parts = [f"Keeper: {watch.name or 'Unnamed'}"]
    parts.append(f"Night {watch.night_count}")
    if watch.weather_mood:
        w = lookup_weather(watch.weather_mood)
        parts.append(f"Weather: {w.get('label', watch.weather_mood)}")
    parts.append("Lamp lit" if watch.lamp_lit else "Lamp not lit")
    if watch.last_task:
        parts.append(f"Last task: {watch.last_task}")
    return " · ".join(parts)


def format_for_prompt(
    watch: KeeperWatch | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not watch:
        return ""
    lines = [
        "Current lighthouse watch:",
        f"- Keeper: {watch.name or 'unnamed'}",
        f"- Night: {watch.night_count}",
        f"- Lamp: {'lit' if watch.lamp_lit else 'unlit'}",
        f"- Story mode: {story_mode}",
        f"- Deck: {card_source}",
    ]
    if watch.weather_mood:
        from src.games.lighthouse.curated import lookup_weather

        w = lookup_weather(watch.weather_mood)
        lines.append(f"- Weather mood: {w.get('label', watch.weather_mood)}")
    if watch.inventory_notes:
        lines.append("- Stored items: " + "; ".join(watch.inventory_notes[:8]))
    return "\n".join(lines)
