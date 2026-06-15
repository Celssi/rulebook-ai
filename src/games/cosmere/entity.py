"""Cosmere character entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


PATH_OPTIONS = [
    {"id": "agent", "label": "Agent"},
    {"id": "hunter", "label": "Hunter"},
    {"id": "leader", "label": "Leader"},
    {"id": "scholar", "label": "Scholar"},
    {"id": "warrior", "label": "Warrior"},
]

ROLE_OPTIONS = [
    {"id": "brawler", "label": "Brawler"},
    {"id": "crafter", "label": "Crafter"},
    {"id": "hunter", "label": "Hunter"},
    {"id": "leader", "label": "Leader"},
    {"id": "scholar", "label": "Scholar"},
    {"id": "survivor", "label": "Survivor"},
    {"id": "warrior", "label": "Warrior"},
]


@dataclass
class CosmereCharacter:
    id: str = ""
    name: str = ""
    path: str = ""
    role: str = ""
    expertises: list[str] = field(default_factory=list)
    plot_dice_pool: int = 0
    deflection: int = 0
    last_roll_summary: str = ""

    def clamp(self) -> None:
        self.name = str(self.name or "").strip()
        self.path = str(self.path or "").strip()
        self.role = str(self.role or "").strip()
        self.plot_dice_pool = max(0, min(10, int(self.plot_dice_pool or 0)))
        self.deflection = max(0, min(20, int(self.deflection or 0)))
        if not isinstance(self.expertises, list):
            self.expertises = []
        self.expertises = [str(x).strip() for x in self.expertises if str(x).strip()][:12]
        self.last_roll_summary = str(self.last_roll_summary or "").strip()

    def header_fields(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "plot_dice_pool": self.plot_dice_pool,
            "deflection": self.deflection,
        }


def default_character() -> CosmereCharacter:
    return CosmereCharacter()


def character_from_dict(data: dict[str, Any] | None) -> CosmereCharacter:
    if not data:
        return default_character()
    expertises = data.get("expertises") or []
    char = CosmereCharacter(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        path=str(data.get("path", "") or ""),
        role=str(data.get("role", "") or ""),
        expertises=[str(x) for x in expertises] if isinstance(expertises, list) else [],
        plot_dice_pool=int(data.get("plot_dice_pool", 0) or 0),
        deflection=int(data.get("deflection", 0) or 0),
        last_roll_summary=str(data.get("last_roll_summary", "") or ""),
    )
    char.clamp()
    return char


def character_to_dict(char: CosmereCharacter) -> dict[str, Any]:
    char.clamp()
    return {
        "id": char.id,
        "name": char.name,
        "path": char.path,
        "role": char.role,
        "expertises": list(char.expertises),
        "plot_dice_pool": char.plot_dice_pool,
        "deflection": char.deflection,
        "last_roll_summary": char.last_roll_summary,
    }


def format_summary(char: CosmereCharacter) -> str:
    parts = [char.name or "Character"]
    if char.path:
        parts.append(char.path.title())
    if char.role:
        parts.append(char.role.title())
    if char.plot_dice_pool:
        parts.append(f"Plot {char.plot_dice_pool}")
    if char.deflection:
        parts.append(f"Def {char.deflection}")
    return " · ".join(parts)


def format_for_prompt(
    char: CosmereCharacter | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not char:
        return ""
    lines = [
        "Current Cosmere character:",
        f"- Name: {char.name or 'unnamed'}",
        f"- Path: {char.path or '(not set)'}",
        f"- Role: {char.role or '(not set)'}",
        f"- Expertises: {', '.join(char.expertises) if char.expertises else '(none)'}",
        f"- Plot dice pool: {char.plot_dice_pool}",
        f"- Deflection: {char.deflection}",
        f"- Story mode: {story_mode}",
        f"- Deck: {card_source}",
    ]
    return "\n".join(lines)


def character_options_payload() -> dict[str, Any]:
    return {"paths": PATH_OPTIONS, "roles": ROLE_OPTIONS}
