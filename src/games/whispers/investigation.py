"""Whispers in the Walls investigation session state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WhispersInvestigation:
    id: str = ""
    investigator_name: str = ""
    background: str = ""
    belonging: str = ""
    location_name: str = ""
    location_title: str = ""
    location_card: str = ""
    difficulty: str = "normal"
    extra_secrets: int = 0
    whispers_deck: list[str] = field(default_factory=list)
    discard_pile: list[str] = field(default_factory=list)
    deck_built: bool = False
    jokers_drawn: int = 0
    turn_number: int = 0
    investigation_complete: bool = False
    force_joker_ending: bool = False
    last_card: str = ""
    last_table: str = ""
    last_title: str = ""
    last_prompt: str = ""

    def clamp(self) -> None:
        self.turn_number = max(0, int(self.turn_number))
        self.jokers_drawn = max(0, min(2, int(self.jokers_drawn)))
        self.extra_secrets = max(0, min(10, int(self.extra_secrets)))
        if self.difficulty not in ("normal", "easy"):
            self.difficulty = "normal"

    def cards_remaining(self) -> int:
        return len(self.whispers_deck)

    def is_ended(self) -> bool:
        return self.investigation_complete or self.force_joker_ending


def default_investigation() -> WhispersInvestigation:
    return WhispersInvestigation()


def investigation_from_dict(data: dict | None) -> WhispersInvestigation:
    if not data:
        return default_investigation()
    inv = WhispersInvestigation(
        id=str(data.get("id", "") or ""),
        investigator_name=str(data.get("investigator_name", "") or ""),
        background=str(data.get("background", "") or ""),
        belonging=str(data.get("belonging", "") or ""),
        location_name=str(data.get("location_name", "") or ""),
        location_title=str(data.get("location_title", "") or ""),
        location_card=str(data.get("location_card", "") or ""),
        difficulty=str(data.get("difficulty", "normal") or "normal"),
        extra_secrets=int(data.get("extra_secrets", 0) or 0),
        whispers_deck=list(data.get("whispers_deck") or []),
        discard_pile=list(data.get("discard_pile") or []),
        deck_built=bool(data.get("deck_built")),
        jokers_drawn=int(data.get("jokers_drawn", 0) or 0),
        turn_number=int(data.get("turn_number", 0) or 0),
        investigation_complete=bool(data.get("investigation_complete")),
        force_joker_ending=bool(data.get("force_joker_ending")),
        last_card=str(data.get("last_card", "") or ""),
        last_table=str(data.get("last_table", "") or ""),
        last_title=str(data.get("last_title", "") or ""),
        last_prompt=str(data.get("last_prompt", "") or ""),
    )
    inv.clamp()
    return inv


def investigation_to_dict(inv: WhispersInvestigation) -> dict[str, Any]:
    inv.clamp()
    return {
        "id": inv.id,
        "investigator_name": inv.investigator_name,
        "background": inv.background,
        "belonging": inv.belonging,
        "location_name": inv.location_name,
        "location_title": inv.location_title,
        "location_card": inv.location_card,
        "difficulty": inv.difficulty,
        "extra_secrets": inv.extra_secrets,
        "whispers_deck": list(inv.whispers_deck),
        "discard_pile": list(inv.discard_pile),
        "deck_built": inv.deck_built,
        "jokers_drawn": inv.jokers_drawn,
        "turn_number": inv.turn_number,
        "investigation_complete": inv.investigation_complete,
        "force_joker_ending": inv.force_joker_ending,
        "last_card": inv.last_card,
        "last_table": inv.last_table,
        "last_title": inv.last_title,
        "last_prompt": inv.last_prompt,
    }


def format_summary(inv: WhispersInvestigation) -> str:
    parts: list[str] = []
    if inv.investigator_name.strip():
        parts.append(inv.investigator_name.strip())
    else:
        parts.append("Investigator")
    if inv.location_name.strip():
        parts.append(inv.location_name.strip())
    elif inv.location_title.strip():
        parts.append(inv.location_title.strip())
    if inv.deck_built:
        parts.append(f"{inv.cards_remaining()} cards left")
    else:
        parts.append("deck not built")
    if inv.is_ended():
        parts.append("investigation ended")
    return " · ".join(parts)


def save_investigation(inv: WhispersInvestigation) -> None:
    from src.games.whispers.play import get_whispers_store

    if not inv.id:
        inv.id = get_whispers_store().roster.get_active_slot_id() or ""
    if inv.id:
        get_whispers_store().save_entity(inv)


def format_for_prompt(
    inv: WhispersInvestigation | None,
    *,
    card_source: str = "virtual",
    story_mode: str = "player",
) -> str:
    if not inv:
        return ""
    lines = [
        "Current Whispers in the Walls investigation:",
        f"- Investigator: {inv.investigator_name.strip() or '(unnamed)'}",
    ]
    if inv.background.strip():
        lines.append(f"- Background: {inv.background.strip()}")
    if inv.belonging.strip():
        lines.append(f"- Belonging: {inv.belonging.strip()}")
    if inv.location_name.strip() or inv.location_title.strip():
        loc = inv.location_name.strip() or inv.location_title.strip()
        lines.append(f"- Location: {loc}")
    lines.append(f"- Difficulty: {inv.difficulty}")
    lines.append(f"- Whispers deck: {inv.cards_remaining()} cards remaining")
    lines.append(f"- Jokers revealed: {inv.jokers_drawn}/2")
    lines.append(
        f"- Story mode: {story_mode} (player = you journal; ai_narrator = AI writes journal prose)"
    )
    if inv.last_prompt:
        lines.append(f"- Last prompt: {inv.last_prompt[:200]}")
    if inv.is_ended():
        lines.append("- Investigation has ended.")
    if card_source == "physical":
        lines.append("- Physical deck mode: user reports card pulls from their Whispers deck.")
    else:
        lines.append("- Virtual deck mode: app draws from the constructed Whispers deck.")
    return "\n".join(lines)
