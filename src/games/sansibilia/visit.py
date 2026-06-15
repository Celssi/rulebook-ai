"""San Sibilia visit entity (journal session state)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class SansibiliaVisit:
    id: str = ""
    name: str = ""
    archetype: str = ""
    character_trait_rank: str = ""
    character_role_rank: str = ""
    character_rank: str = ""
    character_cards: list[str] = field(default_factory=list)
    visit_day: int = 1
    city_changes: int = 0
    city_change_notes: list[str] = field(default_factory=list)
    ending_mode: str = "four_changes"
    score_total: int = 0
    ace_value: int = 11
    last_cards: list[str] = field(default_factory=list)
    last_adjective: str = ""
    last_location_event: str = ""
    days_between: int | None = None
    visit_complete: bool = False

    def clamp(self) -> None:
        self.city_changes = max(0, min(4, int(self.city_changes)))
        self.visit_day = max(1, int(self.visit_day))
        self.score_total = max(0, int(self.score_total))
        if self.ending_mode not in ("four_changes", "score_90"):
            self.ending_mode = "four_changes"
        if self.ace_value not in (1, 11):
            self.ace_value = 11

    def is_ended(self) -> bool:
        if self.visit_complete:
            return True
        if self.ending_mode == "score_90":
            return self.score_total >= 90
        return self.city_changes >= 4


def default_visit() -> SansibiliaVisit:
    return SansibiliaVisit()


def visit_from_dict(data: dict | None) -> SansibiliaVisit:
    if not data:
        return default_visit()
    visit = SansibiliaVisit(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        archetype=str(data.get("archetype", "") or ""),
        character_trait_rank=str(data.get("character_trait_rank", "") or ""),
        character_role_rank=str(data.get("character_role_rank", "") or ""),
        character_rank=str(data.get("character_rank", "") or ""),
        character_cards=list(data.get("character_cards") or []),
        visit_day=int(data.get("visit_day", 1) or 1),
        city_changes=int(data.get("city_changes", 0) or 0),
        city_change_notes=list(data.get("city_change_notes") or []),
        ending_mode=str(data.get("ending_mode", "four_changes") or "four_changes"),
        score_total=int(data.get("score_total", 0) or 0),
        ace_value=int(data.get("ace_value", 11) or 11),
        last_cards=list(data.get("last_cards") or []),
        last_adjective=str(data.get("last_adjective", "") or ""),
        last_location_event=str(data.get("last_location_event", "") or ""),
        days_between=data.get("days_between"),
        visit_complete=bool(data.get("visit_complete")),
    )
    if visit.days_between is not None:
        visit.days_between = int(visit.days_between)
    visit.clamp()
    return visit


def visit_to_dict(visit: SansibiliaVisit) -> dict[str, Any]:
    visit.clamp()
    return {
        "id": visit.id,
        "name": visit.name,
        "archetype": visit.archetype,
        "character_trait_rank": visit.character_trait_rank,
        "character_role_rank": visit.character_role_rank,
        "character_rank": visit.character_rank,
        "character_cards": list(visit.character_cards),
        "visit_day": visit.visit_day,
        "city_changes": visit.city_changes,
        "city_change_notes": list(visit.city_change_notes),
        "ending_mode": visit.ending_mode,
        "score_total": visit.score_total,
        "ace_value": visit.ace_value,
        "last_cards": list(visit.last_cards),
        "last_adjective": visit.last_adjective,
        "last_location_event": visit.last_location_event,
        "days_between": visit.days_between,
        "visit_complete": visit.visit_complete,
    }


def format_summary(visit: SansibiliaVisit) -> str:
    parts = [f"Day {visit.visit_day}"]
    if visit.name.strip():
        parts.append(visit.name.strip())
    elif visit.archetype.strip():
        parts.append(visit.archetype.strip())
    else:
        parts.append("Visitor")
    parts.append(f"changes {visit.city_changes}/4")
    if visit.ending_mode == "score_90":
        parts.append(f"score {visit.score_total}/90")
    if visit.is_ended():
        parts.append("visit ended")
    return " · ".join(parts)


def save_visit(visit: SansibiliaVisit) -> None:
    from src.games.sansibilia.play import get_sansibilia_store

    if not visit.id:
        visit.id = get_sansibilia_store().roster.get_active_slot_id() or ""
    if visit.id:
        get_sansibilia_store().save_entity(visit)


def format_for_prompt(
    visit: SansibiliaVisit | None,
    *,
    card_source: str = "virtual",
    story_mode: str = "player",
) -> str:
    if not visit:
        return ""
    lines = [
        "Current San Sibilia visit (solo journaling — use for card draws and city-change checks):",
        f"- Name: {visit.name.strip() or '(unnamed)'}",
    ]
    if visit.archetype.strip():
        lines.append(f"- Archetype: {visit.archetype.strip()}")
    lines.append(f"- Journal day: {visit.visit_day}")
    lines.append(f"- City changes checked: {visit.city_changes}/4")
    lines.append(f"- Ending mode: {visit.ending_mode}")
    lines.append(
        f"- Story mode: {story_mode} (player = you journal; ai_narrator = AI writes journal prose on draws)"
    )
    if visit.ending_mode == "score_90":
        lines.append(f"- Score tally: {visit.score_total}/90 (ace counts as {visit.ace_value})")
    if visit.last_adjective or visit.last_location_event:
        lines.append(
            f"- Last draw: {visit.last_adjective} + {visit.last_location_event}".strip(" +")
        )
    if visit.is_ended():
        lines.append("- Visit has ended — use ending journal prompts.")
    if card_source == "physical":
        lines.append("- Physical deck mode: user reports card pulls; do not invent draws.")
    else:
        lines.append("- Virtual deck mode: tool draws are authoritative.")
    return "\n".join(lines)
