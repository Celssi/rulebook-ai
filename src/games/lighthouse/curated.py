"""Curated Lighthouse card tables (not indexed in Chroma)."""

from __future__ import annotations

import random
import re
from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR

_CARD_RE = re.compile(
    r"(?i)^(?P<rank>ace|a|king|k|queen|q|jack|j|[2-9]|10)\s+of\s+"
    r"(?P<suit>hearts|diamonds|clubs|spades)$"
)
_RANK_ALIASES = {
    "a": "ace",
    "ace": "ace",
    "j": "jack",
    "jack": "jack",
    "q": "queen",
    "queen": "queen",
    "k": "king",
    "king": "king",
    **{str(n): str(n) for n in range(2, 11)},
}
_RED_SUITS = frozenset({"hearts", "diamonds"})
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_EVENT_RANKS = _ALL_RANKS


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _weather() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("lighthouse_weather.yaml").get("moods") or {})


@lru_cache(maxsize=1)
def _maintenance() -> dict[str, Any]:
    return _load_yaml("lighthouse_maintenance.yaml")


@lru_cache(maxsize=1)
def _observation() -> dict[str, Any]:
    return _load_yaml("lighthouse_observation.yaml")


@lru_cache(maxsize=1)
def _events() -> dict[str, Any]:
    return _load_yaml("lighthouse_events.yaml")


@lru_cache(maxsize=1)
def _beachcombing() -> dict[str, Any]:
    return _load_yaml("lighthouse_beachcombing.yaml")


@lru_cache(maxsize=1)
def _play() -> dict[str, Any]:
    return _load_yaml("lighthouse_play.yaml")


def parse_playing_card(card: str) -> dict[str, Any] | None:
    m = _CARD_RE.match(card.strip())
    if not m:
        return None
    raw_rank = m.group("rank").lower()
    rank_key = _RANK_ALIASES.get(raw_rank, raw_rank)
    suit = m.group("suit").lower()
    color = "red" if suit in _RED_SUITS else "black"
    return {
        "suit": suit,
        "rank_key": rank_key,
        "color": color,
        "card": card.strip(),
        "is_red": color == "red",
    }


def flip_coin() -> dict[str, Any]:
    heads = random.choice([True, False])
    side = "heads" if heads else "tails"
    return {"ok": True, "heads": heads, "side": side, "summary": f"Coin: **{side}**"}


def weather_options() -> list[dict[str, str]]:
    moods = _weather()
    return [
        {"id": mid, "label": str(data.get("label", mid)), "description": str(data.get("description", ""))}
        for mid, data in moods.items()
        if isinstance(data, dict)
    ]


def lookup_weather(mood_id: str) -> dict[str, str]:
    data = _weather().get(mood_id) or {}
    return {
        "id": mood_id,
        "label": str(data.get("label", mood_id)),
        "description": str(data.get("description", "")),
    }


def lookup_maintenance_task(roll: int) -> str:
    key = str(max(1, min(6, roll)))
    return str((_maintenance().get("tasks") or {}).get(key, ""))


def lookup_maintenance_suit(suit: str) -> str:
    return str((_maintenance().get("suit_outcomes") or {}).get(suit.lower(), ""))


def lookup_observation_subject(roll: int) -> str:
    key = str(max(1, min(6, roll)))
    return str((_observation().get("subjects") or {}).get(key, ""))


def lookup_observation_distance(suit: str) -> str:
    return str((_observation().get("suit_distance") or {}).get(suit.lower(), ""))


def lookup_event(rank_key: str) -> str:
    return str((_events().get("ranks") or {}).get(rank_key, ""))


def lookup_event_severity(color: str) -> str:
    return str((_events().get("severity") or {}).get(color, ""))


def lookup_beachcombing_item(rank_key: str) -> str:
    return str((_beachcombing().get("ranks") or {}).get(rank_key, ""))


def lookup_beachcombing_source(color: str) -> str:
    return str((_beachcombing().get("source") or {}).get(color, ""))


def beachcombing_card_count(hour: int) -> int:
    """Glance at the hour; divide by two, round up (p.20)."""
    h = max(0, min(23, hour))
    return (h + 1) // 2


def format_light_lamp(card: str, coin: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    lit = bool(coin.get("heads")) and bool(parsed and parsed["is_red"])
    return {
        "card": card,
        "coin": coin.get("side", ""),
        "lit": lit,
        "parsed": parsed,
        "message": (
            "**Lamp lit!** Heads and a red card — the wick catches."
            if lit
            else f"**Not yet.** Coin: {coin.get('side', '?')}, card: {card}"
            + (" (need heads + red)" if parsed else "")
        ),
    }


def format_maintenance(roll: int, card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    suit = parsed["suit"] if parsed else ""
    task = lookup_maintenance_task(roll)
    outcome = lookup_maintenance_suit(suit) if suit else ""
    return {
        "roll": roll,
        "card": card,
        "task": task,
        "outcome": outcome,
        "suit": suit,
        "prompt": f"{task} {outcome}".strip(),
    }


def format_observation(roll: int, card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    suit = parsed["suit"] if parsed else ""
    subject = lookup_observation_subject(roll)
    distance = lookup_observation_distance(suit) if suit else ""
    return {
        "roll": roll,
        "card": card,
        "subject": subject,
        "distance": distance,
        "suit": suit,
        "prompt": f"{subject} {distance}".strip(),
    }


def format_event(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "event": "", "severity": "", "prompt": ""}
    event = lookup_event(parsed["rank_key"])
    severity = lookup_event_severity(parsed["color"])
    return {
        "card": card,
        "rank_key": parsed["rank_key"],
        "color": parsed["color"],
        "event": event,
        "severity": severity,
        "prompt": f"({parsed['color']} — {severity}) {event}".strip(),
    }


def format_beachcombing_find(card: str, coin: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "item": "", "source": "", "coin": coin.get("side", ""), "prompt": ""}
    item = lookup_beachcombing_item(parsed["rank_key"])
    source = lookup_beachcombing_source(parsed["color"])
    return {
        "card": card,
        "item": item,
        "source": source,
        "coin": coin.get("side", ""),
        "prompt": f"{item} ({source}) — coin: {coin.get('side', '?')} for condition.",
    }


def task_routing_text() -> str:
    rows = _play().get("task_routing") or []
    lines = ["**Choose a task by the feel of the night (p.11):**", ""]
    for row in rows:
        if isinstance(row, dict):
            lines.append(f"- If the night is **{row.get('night', '')}** → **{row.get('section', '')}**")
    return "\n".join(lines)


def ending_text() -> str:
    rows = _play().get("ending_shuffles") or []
    lines = [
        "**Ending your watch (p.18)**",
        "",
        "Extinguish the lighthouse light. Shuffle the deck as you reflect:",
        "",
    ]
    for row in rows:
        if isinstance(row, dict):
            lines.append(f"- **{row.get('label', '')}** — shuffle **{row.get('shuffles', 1)}** time(s)")
    lines.extend(
        [
            "",
            "Finish your logbook entry. How do you feel? Did you achieve or resolve anything?",
        ]
    )
    return "\n".join(lines)


def order_of_play_text() -> str:
    return """**Order of play (p.5)**

**Set up (once per session):** Initial observations → weather → lighting the light.

**Playing:** Choose Observation, Maintenance, or Event tasks; record each in the logbook; repeat.

**Ending:** When satisfied, extinguish the light, shuffle per the night's intensity, and close your entry.

**Needs:** d6, playing cards, a coin, and a journal (logbook)."""


def all_event_ranks_valid() -> bool:
    ranks = _events().get("ranks") or {}
    return all(r in ranks for r in _EVENT_RANKS)


def all_beachcombing_ranks_valid() -> bool:
    ranks = _beachcombing().get("ranks") or {}
    return all(r in ranks for r in _EVENT_RANKS)
