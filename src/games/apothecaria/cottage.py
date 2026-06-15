"""Witch cottage entity for Apothecaria play sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

def default_tools() -> list[str]:
    return ["mortar", "cauldron", "alembic"]


@dataclass
class WitchCottage:
    id: str = ""
    name: str = ""
    reputation: int = 5
    silver: int = 0
    season: str = "spring"
    week: int = 1
    phase: str = "idle"  # idle | ailment | downtime | festival | consequence
    downtime_timer: int = 0
    current_locale: str = "glimmerwood"
    foraging_tracks: dict[str, int] = field(default_factory=dict)
    patient_name: str = ""
    patient_job: str = ""
    patient_type: str = ""
    ailment_name: str = ""
    ailment_tags: list[str] = field(default_factory=list)
    ailment_timer: int | None = None
    ailment_potency: int = 1
    familiar_type: str = ""
    familiar_skill: str = ""
    inventory: list[dict[str, Any]] = field(default_factory=list)
    tools_owned: list[str] = field(default_factory=default_tools)
    upgrades_owned: list[str] = field(default_factory=list)
    unlocks: list[str] = field(default_factory=list)
    hunting_reagent: str = ""
    hunting_fv: int | None = None
    potion_poison: int = 0
    potion_sweet: int = 0
    turn_count: int = 0
    seen_events: list[str] = field(default_factory=list)
    golem_repair: int = 0
    moonstone_segments: int = 4
    storyline_table: str = "first_steps"
    joker_clues: int = 0
    last_cards: list[str] = field(default_factory=list)
    last_draw_kind: str = ""

    def clamp(self) -> None:
        self.reputation = max(0, int(self.reputation or 0))
        self.silver = max(0, int(self.silver or 0))
        self.week = max(1, min(13, int(self.week or 1)))
        if self.season not in ("spring", "summer", "autumn", "winter"):
            self.season = "spring"
        if self.phase not in ("idle", "ailment", "downtime", "festival", "consequence"):
            self.phase = "idle"
        self.downtime_timer = max(0, min(6, int(self.downtime_timer or 0)))
        if self.ailment_timer is not None:
            self.ailment_timer = max(0, int(self.ailment_timer))
        self.name = str(self.name or "").strip()
        self.moonstone_segments = max(0, min(4, int(self.moonstone_segments or 0)))
        self.golem_repair = max(0, int(self.golem_repair or 0))
        if not isinstance(self.ailment_tags, list):
            self.ailment_tags = []
        if not isinstance(self.inventory, list):
            self.inventory = []
        if not isinstance(self.tools_owned, list):
            self.tools_owned = default_tools()
        if not isinstance(self.upgrades_owned, list):
            self.upgrades_owned = []
        if not isinstance(self.unlocks, list):
            self.unlocks = []
        if not isinstance(self.foraging_tracks, dict):
            self.foraging_tracks = {}
        if not isinstance(self.seen_events, list):
            self.seen_events = []
        if not isinstance(self.last_cards, list):
            self.last_cards = []


def default_cottage() -> WitchCottage:
    return WitchCottage()


def cottage_from_dict(data: dict[str, Any] | None) -> WitchCottage:
    if not data:
        return default_cottage()
    timer = data.get("ailment_timer")
    tools = data.get("tools_owned")
    return WitchCottage(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        reputation=int(data.get("reputation", 5) or 5),
        silver=int(data.get("silver", 0) or 0),
        season=str(data.get("season", "spring") or "spring"),
        week=int(data.get("week", 1) or 1),
        phase=str(data.get("phase", "idle") or "idle"),
        downtime_timer=int(data.get("downtime_timer", 0) or 0),
        current_locale=str(data.get("current_locale", "glimmerwood") or "glimmerwood"),
        foraging_tracks=dict(data.get("foraging_tracks") or {}),
        patient_name=str(data.get("patient_name", "") or ""),
        patient_job=str(data.get("patient_job", "") or ""),
        patient_type=str(data.get("patient_type", "") or ""),
        ailment_name=str(data.get("ailment_name", "") or ""),
        ailment_tags=[str(t) for t in (data.get("ailment_tags") or [])],
        ailment_timer=int(timer) if timer is not None else None,
        ailment_potency=int(data.get("ailment_potency", 1) or 1),
        familiar_type=str(data.get("familiar_type", "") or ""),
        familiar_skill=str(data.get("familiar_skill", "") or ""),
        inventory=list(data.get("inventory") or []),
        tools_owned=list(tools) if tools else default_tools(),
        upgrades_owned=[str(u) for u in (data.get("upgrades_owned") or [])],
        unlocks=[str(u) for u in (data.get("unlocks") or [])],
        hunting_reagent=str(data.get("hunting_reagent", "") or ""),
        hunting_fv=data.get("hunting_fv"),
        potion_poison=int(data.get("potion_poison", 0) or 0),
        potion_sweet=int(data.get("potion_sweet", 0) or 0),
        turn_count=int(data.get("turn_count", 0) or 0),
        seen_events=[str(x) for x in (data.get("seen_events") or [])],
        golem_repair=int(data.get("golem_repair", 0) or 0),
        moonstone_segments=int(data.get("moonstone_segments", 4) or 4),
        storyline_table=str(data.get("storyline_table", "first_steps") or "first_steps"),
        joker_clues=int(data.get("joker_clues", 0) or 0),
        last_cards=[str(c) for c in (data.get("last_cards") or [])],
        last_draw_kind=str(data.get("last_draw_kind", "") or ""),
    )


def cottage_to_dict(cottage: WitchCottage) -> dict[str, Any]:
    cottage.clamp()
    return {
        "id": cottage.id,
        "name": cottage.name,
        "reputation": cottage.reputation,
        "silver": cottage.silver,
        "season": cottage.season,
        "week": cottage.week,
        "phase": cottage.phase,
        "downtime_timer": cottage.downtime_timer,
        "current_locale": cottage.current_locale,
        "foraging_tracks": dict(cottage.foraging_tracks),
        "patient_name": cottage.patient_name,
        "patient_job": cottage.patient_job,
        "patient_type": cottage.patient_type,
        "ailment_name": cottage.ailment_name,
        "ailment_tags": list(cottage.ailment_tags),
        "ailment_timer": cottage.ailment_timer,
        "ailment_potency": cottage.ailment_potency,
        "familiar_type": cottage.familiar_type,
        "familiar_skill": cottage.familiar_skill,
        "inventory": list(cottage.inventory),
        "tools_owned": list(cottage.tools_owned),
        "upgrades_owned": list(cottage.upgrades_owned),
        "unlocks": list(cottage.unlocks),
        "hunting_reagent": cottage.hunting_reagent,
        "hunting_fv": cottage.hunting_fv,
        "potion_poison": cottage.potion_poison,
        "potion_sweet": cottage.potion_sweet,
        "turn_count": cottage.turn_count,
        "seen_events": list(cottage.seen_events),
        "golem_repair": cottage.golem_repair,
        "moonstone_segments": cottage.moonstone_segments,
        "storyline_table": cottage.storyline_table,
        "joker_clues": cottage.joker_clues,
        "last_cards": list(cottage.last_cards),
        "last_draw_kind": cottage.last_draw_kind,
    }


def format_summary(cottage: WitchCottage) -> str:
    from src.games.apothecaria.curated import reputation_tier_label

    parts = [f"Witch: {cottage.name or 'Unnamed'}"]
    parts.append(f"Rep {cottage.reputation} ({reputation_tier_label(cottage.reputation)})")
    parts.append(f"Wk {cottage.week} {cottage.season.title()}")
    if cottage.silver:
        parts.append(f"{cottage.silver} Silver")
    if cottage.phase != "idle":
        parts.append(cottage.phase.replace("_", " "))
    if cottage.ailment_name:
        timer = f" T{cottage.ailment_timer}" if cottage.ailment_timer is not None else ""
        parts.append(f"{cottage.ailment_name}{timer}")
    if cottage.hunting_reagent:
        parts.append(f"Hunting {cottage.hunting_reagent}")
    return " · ".join(parts)


def format_for_prompt(
    cottage: WitchCottage | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not cottage:
        return ""
    from src.games.apothecaria.curated import reputation_tier_label
    from src.games.apothecaria.game_logic import foraging_points_for_locale

    lines = [
        "Current Apothecaria cottage:",
        f"- Witch: {cottage.name or 'unnamed'}",
        f"- Reputation: {cottage.reputation} ({reputation_tier_label(cottage.reputation)})",
        f"- Calendar: week {cottage.week} of {cottage.season} — phase: {cottage.phase}",
        f"- Silver: {cottage.silver}",
        f"- Locale: {cottage.current_locale}",
        f"- Foraging points ({cottage.current_locale}): {foraging_points_for_locale(cottage)}",
        f"- Story mode: {story_mode}",
        f"- Deck: {card_source}",
    ]
    if cottage.inventory:
        names = ", ".join(str(i.get("name", "")) for i in cottage.inventory[:6])
        lines.append(f"- Inventory: {names}")
    if cottage.tools_owned:
        lines.append(f"- Tools: {', '.join(cottage.tools_owned)}")
    if cottage.patient_name or cottage.ailment_name:
        lines.append(f"- Patient: {cottage.patient_name or '?'} ({cottage.patient_type or '?'})")
        if cottage.ailment_name:
            tag_str = ", ".join(f"[{t}]" for t in cottage.ailment_tags)
            timer = cottage.ailment_timer if cottage.ailment_timer is not None else "none"
            lines.append(f"- Ailment: {cottage.ailment_name} {tag_str} timer {timer}")
    if cottage.hunting_reagent:
        lines.append(f"- Hunting: {cottage.hunting_reagent} (FV {cottage.hunting_fv})")
    if cottage.familiar_type:
        lines.append(f"- Familiar: {cottage.familiar_type}")
    return "\n".join(lines)
