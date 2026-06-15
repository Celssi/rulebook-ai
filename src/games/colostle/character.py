"""Colostle adventurer entity."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.games.colostle.curated import class_options, lookup_class


@dataclass
class ColostleCharacter:
    id: str = ""
    name: str = ""
    look: str = ""
    character_class: str = ""
    calling: str = ""
    nature: str = ""
    calling_card: str = ""
    nature_card: str = ""
    weapon: str = ""
    exploration_score: int = 3
    combat_score: int = 3
    wounds: int = 0
    treasures: int = 0
    chapter: int = 1
    location_mode: str = "roomlands"  # roomlands | ocean | city | battlements
    inventory_notes: list[str] = field(default_factory=list)
    last_cards: list[str] = field(default_factory=list)
    last_task: str = ""

    def clamp(self) -> None:
        self.chapter = max(1, int(self.chapter or 1))
        self.exploration_score = max(0, min(5, int(self.exploration_score or 0)))
        self.combat_score = max(0, min(5, int(self.combat_score or 0)))
        self.wounds = max(0, int(self.wounds or 0))
        self.treasures = max(0, int(self.treasures or 0))
        self.name = str(self.name or "").strip()
        self.look = str(self.look or "").strip()
        self.weapon = str(self.weapon or "").strip()
        self.calling = str(self.calling or "").strip()
        self.nature = str(self.nature or "").strip()
        if self.location_mode not in ("roomlands", "ocean", "city", "battlements"):
            self.location_mode = "roomlands"
        if self.character_class:
            stats = lookup_class(self.character_class)
            if stats["exploration"] and not self.exploration_score:
                self.exploration_score = stats["exploration"]
            if stats["combat"] and not self.combat_score:
                self.combat_score = stats["combat"]

    def apply_class(self, class_id: str) -> None:
        stats = lookup_class(class_id)
        self.character_class = class_id
        self.exploration_score = int(stats.get("exploration", 3))
        self.combat_score = int(stats.get("combat", 3))


def default_character() -> ColostleCharacter:
    return ColostleCharacter()


def character_from_dict(data: dict[str, Any] | None) -> ColostleCharacter:
    if not data:
        return default_character()
    inv = data.get("inventory_notes") or []
    cards = data.get("last_cards") or []
    char = ColostleCharacter(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        look=str(data.get("look", "") or ""),
        character_class=str(data.get("character_class", "") or ""),
        calling=str(data.get("calling", "") or ""),
        nature=str(data.get("nature", "") or ""),
        calling_card=str(data.get("calling_card", "") or ""),
        nature_card=str(data.get("nature_card", "") or ""),
        weapon=str(data.get("weapon", "") or ""),
        exploration_score=int(data.get("exploration_score", 3) or 3),
        combat_score=int(data.get("combat_score", 3) or 3),
        wounds=int(data.get("wounds", 0) or 0),
        treasures=int(data.get("treasures", 0) or 0),
        chapter=int(data.get("chapter", 1) or 1),
        location_mode=str(data.get("location_mode", "roomlands") or "roomlands"),
        inventory_notes=[str(x) for x in inv] if isinstance(inv, list) else [],
        last_task=str(data.get("last_task", "") or ""),
        last_cards=[str(x) for x in cards] if isinstance(cards, list) else [],
    )
    char.clamp()
    return char


def character_to_dict(char: ColostleCharacter) -> dict[str, Any]:
    char.clamp()
    return {
        "id": char.id,
        "name": char.name,
        "look": char.look,
        "character_class": char.character_class,
        "calling": char.calling,
        "nature": char.nature,
        "calling_card": char.calling_card,
        "nature_card": char.nature_card,
        "weapon": char.weapon,
        "exploration_score": char.exploration_score,
        "combat_score": char.combat_score,
        "wounds": char.wounds,
        "treasures": char.treasures,
        "chapter": char.chapter,
        "location_mode": char.location_mode,
        "inventory_notes": list(char.inventory_notes),
        "last_task": char.last_task,
        "last_cards": list(char.last_cards),
    }


def format_summary(char: ColostleCharacter) -> str:
    cls = lookup_class(char.character_class) if char.character_class else {}
    label = cls.get("label", char.character_class or "Unclassed")
    parts = [
        f"{char.name or 'Adventurer'}",
        label,
        f"Ch.{char.chapter}",
        f"Exp {char.exploration_score}",
        f"Combat {char.combat_score}",
    ]
    if char.wounds:
        parts.append(f"Wounds {char.wounds}")
    if char.treasures:
        parts.append(f"Treasures {char.treasures}")
    return " · ".join(parts)


def format_for_prompt(
    char: ColostleCharacter | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not char:
        return ""
    cls = lookup_class(char.character_class) if char.character_class else {}
    lines = [
        "Current Colostle adventurer:",
        f"- Name: {char.name or 'unnamed'}",
        f"- Class: {cls.get('label', char.character_class or 'unset')}",
        f"- Calling: {char.calling or '(not set)'}",
        f"- Nature: {char.nature or '(not set)'}",
        f"- Weapon: {char.weapon or '(not set)'}",
        f"- Chapter: {char.chapter}",
        f"- Exploration score: {char.exploration_score}",
        f"- Combat score: {char.combat_score}",
        f"- Wounds: {char.wounds}",
        f"- Treasures: {char.treasures}",
        f"- Location mode: {char.location_mode}",
        f"- Story mode: {story_mode}",
        f"- Deck: {card_source}",
    ]
    if char.inventory_notes:
        lines.append("- Inventory: " + "; ".join(char.inventory_notes[:8]))
    return "\n".join(lines)


def class_options_payload() -> list[dict[str, Any]]:
    return class_options()
