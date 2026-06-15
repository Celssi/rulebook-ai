"""The One Ring Strider Mode hero entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

CULTURE_OPTIONS = [
    {"id": "hobbit", "label": "Hobbits of the Shire"},
    {"id": "barding", "label": "Bardings"},
    {"id": "dwarf", "label": "Dwarves of Durin's Folk"},
    {"id": "elf", "label": "Elves of Lindon"},
    {"id": "men_of_bree", "label": "Men of Bree"},
    {"id": "ranger", "label": "Rangers of the North"},
    {"id": "other", "label": "Other"},
]

CALLING_OPTIONS = [
    {"id": "captain", "label": "Captain"},
    {"id": "champion", "label": "Champion"},
    {"id": "messenger", "label": "Messenger"},
    {"id": "scholar", "label": "Scholar"},
    {"id": "treasure_hunter", "label": "Treasure Hunter"},
    {"id": "warden", "label": "Warden"},
]

PATRON_OPTIONS = [
    {"id": "bilbo", "label": "Bilbo Baggins"},
    {"id": "gandalf", "label": "Gandalf the Grey"},
    {"id": "gilraen", "label": "Gilraen"},
    {"id": "balin", "label": "Balin, Son of Fundin"},
    {"id": "cirdan", "label": "Círdan the Shipwright"},
    {"id": "tom_goldberry", "label": "Tom Bombadil & Goldberry"},
]

HUNT_REGION_OPTIONS = [
    {"id": "border", "label": "Border Land"},
    {"id": "wild", "label": "Wild Land"},
    {"id": "dark", "label": "Dark Land"},
]


@dataclass
class TorHero:
    id: str = ""
    name: str = ""
    culture: str = ""
    calling: str = ""
    hope: int = 0
    dread: int = 0
    weary: bool = False
    strider: bool = True
    eye_awareness: int = 0
    patron: str = ""
    safe_haven: str = ""
    journey_day: int = 0
    hunt_region: str = "wild"
    last_roll_summary: str = ""

    def clamp(self) -> None:
        self.name = str(self.name or "").strip()
        self.culture = str(self.culture or "").strip()
        self.calling = str(self.calling or "").strip()
        self.hope = max(0, min(20, int(self.hope or 0)))
        self.dread = max(0, min(20, int(self.dread or 0)))
        self.weary = bool(self.weary)
        self.strider = bool(self.strider)
        self.eye_awareness = max(0, min(20, int(self.eye_awareness or 0)))
        self.patron = str(self.patron or "").strip()
        self.safe_haven = str(self.safe_haven or "").strip()
        self.journey_day = max(0, min(999, int(self.journey_day or 0)))
        region = str(self.hunt_region or "wild").strip().lower()
        if region not in ("border", "wild", "dark"):
            region = "wild"
        self.hunt_region = region
        self.last_roll_summary = str(self.last_roll_summary or "").strip()

    def header_fields(self) -> dict[str, Any]:
        return {
            "culture": self.culture,
            "calling": self.calling,
            "hope": self.hope,
            "dread": self.dread,
            "weary": self.weary,
            "strider": self.strider,
            "eye_awareness": self.eye_awareness,
            "patron": self.patron,
            "safe_haven": self.safe_haven,
            "journey_day": self.journey_day,
            "hunt_region": self.hunt_region,
        }


def default_hero() -> TorHero:
    return TorHero()


def hero_from_dict(data: dict[str, Any] | None) -> TorHero:
    if not data:
        return default_hero()
    hero = TorHero(
        id=str(data.get("id", "") or ""),
        name=str(data.get("name", "") or ""),
        culture=str(data.get("culture", "") or ""),
        calling=str(data.get("calling", "") or ""),
        hope=int(data.get("hope", 0) or 0),
        dread=int(data.get("dread", 0) or 0),
        weary=bool(data.get("weary", False)),
        strider=bool(data.get("strider", True)),
        eye_awareness=int(data.get("eye_awareness", 0) or 0),
        patron=str(data.get("patron", "") or ""),
        safe_haven=str(data.get("safe_haven", "") or ""),
        journey_day=int(data.get("journey_day", 0) or 0),
        hunt_region=str(data.get("hunt_region", "wild") or "wild"),
        last_roll_summary=str(data.get("last_roll_summary", "") or ""),
    )
    hero.clamp()
    return hero


def hero_to_dict(hero: TorHero) -> dict[str, Any]:
    hero.clamp()
    return {
        "id": hero.id,
        "name": hero.name,
        "culture": hero.culture,
        "calling": hero.calling,
        "hope": hero.hope,
        "dread": hero.dread,
        "weary": hero.weary,
        "strider": hero.strider,
        "eye_awareness": hero.eye_awareness,
        "patron": hero.patron,
        "safe_haven": hero.safe_haven,
        "journey_day": hero.journey_day,
        "hunt_region": hero.hunt_region,
        "last_roll_summary": hero.last_roll_summary,
    }


def format_summary(hero: TorHero) -> str:
    parts = [hero.name or "Hero"]
    if hero.culture:
        parts.append(hero.culture.replace("_", " ").title())
    if hero.calling:
        parts.append(hero.calling.replace("_", " ").title())
    if hero.hope:
        parts.append(f"Hope {hero.hope}")
    if hero.dread:
        parts.append(f"Dread {hero.dread}")
    if hero.eye_awareness:
        parts.append(f"Eye {hero.eye_awareness}")
    if hero.journey_day:
        parts.append(f"Day {hero.journey_day}")
    return " · ".join(parts)


def format_for_prompt(
    hero: TorHero | None,
    *,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    if not hero:
        return ""
    lines = [
        "Current One Ring Strider Mode hero:",
        f"- Name: {hero.name or 'unnamed'}",
        f"- Culture: {hero.culture or '(not set)'}",
        f"- Calling: {hero.calling or '(not set)'}",
        f"- Hope: {hero.hope}",
        f"- Dread (Shadow): {hero.dread}",
        f"- Weary: {'yes' if hero.weary else 'no'}",
        f"- Strider (Inspired on journey skill rolls): {'yes' if hero.strider else 'no'}",
        f"- Eye Awareness: {hero.eye_awareness}",
        f"- Patron: {hero.patron or '(not set)'}",
        f"- Safe Haven: {hero.safe_haven or '(not set)'}",
        f"- Journey day: {hero.journey_day}",
        f"- Hunt region: {hero.hunt_region}",
        f"- Story mode: {story_mode}",
        f"- Deck: {card_source}",
    ]
    return "\n".join(lines)


def character_options_payload() -> dict[str, Any]:
    return {
        "cultures": CULTURE_OPTIONS,
        "patrons": PATRON_OPTIONS,
        "callings": CALLING_OPTIONS,
        "hunt_regions": HUNT_REGION_OPTIONS,
    }
