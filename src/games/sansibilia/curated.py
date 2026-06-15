"""Curated San Sibilia card tables and prompts (not indexed in Chroma)."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from src.settings import CURATED_DIR

_CARD_RE = re.compile(
    r"(?i)^(?P<rank>ace|a|king|k|queen|q|jack|j|[2-9]|10)\s+of\s+(?P<suit>hearts|diamonds|clubs|spades)$"
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
_BLACK_SUITS = frozenset({"clubs", "spades"})
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _character_table() -> dict[str, dict[str, str]]:
    raw = _load_yaml("sansibilia_character_table.yaml").get("ranks") or {}
    out: dict[str, dict[str, str]] = {}
    for rank, entry in raw.items():
        if isinstance(entry, dict):
            out[str(rank)] = {
                "trait": str(entry.get("trait", "")),
                "role": str(entry.get("role", "")),
            }
        else:
            out[str(rank)] = {"trait": "", "role": str(entry)}
    return out


@lru_cache(maxsize=1)
def _adjective_tables() -> dict[str, dict[str, str]]:
    data = _load_yaml("sansibilia_adjective_tables.yaml")
    out: dict[str, dict[str, str]] = {}
    for color in ("red", "black"):
        block = data.get(color) or {}
        out[color] = {str(k): str(v) for k, v in block.items()}
    return out


@lru_cache(maxsize=1)
def _location_tables() -> dict[str, dict[str, str]]:
    data = _load_yaml("sansibilia_location_event_tables.yaml")
    out: dict[str, dict[str, str]] = {}
    for color in ("red", "black"):
        block = data.get(color) or {}
        out[color] = {str(k): str(v) for k, v in block.items()}
    return out


@lru_cache(maxsize=1)
def _city_changes() -> dict[str, Any]:
    return _load_yaml("sansibilia_city_changes.yaml")


@lru_cache(maxsize=1)
def _journal_prompts() -> dict[str, Any]:
    return _load_yaml("sansibilia_journal_prompts.yaml")


@lru_cache(maxsize=1)
def _ending_modes() -> dict[str, Any]:
    return _load_yaml("sansibilia_ending_modes.yaml")


def parse_playing_card(card: str) -> dict[str, Any] | None:
    m = _CARD_RE.match(card.strip())
    if not m:
        return None
    raw_rank = m.group("rank").lower()
    rank_key = _RANK_ALIASES.get(raw_rank, raw_rank)
    suit = m.group("suit").lower()
    if rank_key == "ace":
        numeric = 11
    elif rank_key in ("jack", "queen", "king"):
        numeric = 10
    else:
        numeric = int(rank_key)
    color = "red" if suit in _RED_SUITS else "black"
    return {
        "suit": suit,
        "rank_key": rank_key,
        "numeric_value": numeric,
        "color": color,
        "card": card.strip(),
    }


def suit_color(suit: str) -> str:
    return "red" if suit in _RED_SUITS else "black"


def rank_numeric(rank_key: str, *, ace_as: int = 11) -> int:
    if rank_key == "ace":
        return ace_as
    if rank_key in ("jack", "queen", "king"):
        return 10
    return int(rank_key)


def higher_rank_card(cards: list[str]) -> str | None:
    parsed = [parse_playing_card(c) for c in cards]
    valid = [p for p in parsed if p]
    if not valid:
        return None
    best = max(valid, key=lambda p: p["numeric_value"])
    return str(best["card"])


def _word_title(text: str) -> str:
    return " ".join(part.capitalize() for part in text.split())


def lookup_character_trait(rank_key: str) -> str:
    return _character_table().get(rank_key, {}).get("trait", "")


def lookup_character_role(rank_key: str) -> str:
    return _character_table().get(rank_key, {}).get("role", "")


def format_character_archetype(trait: str, role: str) -> str:
    if not trait or not role:
        return ""
    return f"{_word_title(trait)} {role.lower()}"


def lookup_adjective(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    return _adjective_tables().get(parsed["color"], {}).get(parsed["rank_key"], "")


def lookup_location_event(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    return _location_tables().get(parsed["color"], {}).get(parsed["rank_key"], "")


def detect_city_change(card1: str, card2: str) -> dict[str, Any] | None:
    a, b = parse_playing_card(card1), parse_playing_card(card2)
    if not a or not b:
        return None
    changes = _city_changes()
    if a["suit"] == b["suit"]:
        block = (changes.get("same_suit") or {}).get(a["suit"])
        if isinstance(block, dict):
            return {
                "kind": "same_suit",
                "suit": a["suit"],
                "title": block.get("title", ""),
                "prompt": block.get("prompt", ""),
            }
    if a["rank_key"] == b["rank_key"]:
        block = changes.get("same_value") or {}
        return {
            "kind": "same_value",
            "rank_key": a["rank_key"],
            "title": block.get("title", ""),
            "prompt": block.get("prompt", ""),
        }
    return None


def day_one_prompts() -> list[str]:
    block = _journal_prompts().get("day_one") or {}
    return list(block.get("questions") or [])


def ending_prompts() -> list[str]:
    block = _journal_prompts().get("ending") or {}
    return list(block.get("questions") or [])


def ending_mode_options() -> list[dict[str, str]]:
    modes = (_ending_modes().get("modes") or {}).values()
    return [
        {"id": str(m.get("id", "")), "label": str(m.get("label", ""))}
        for m in modes
        if isinstance(m, dict) and m.get("id")
    ]


def character_trait_options() -> list[dict[str, str]]:
    table = _character_table()
    return [
        {"id": rank, "label": _word_title(table[rank]["trait"])}
        for rank in _ALL_RANKS
        if rank in table and table[rank].get("trait")
    ]


def character_role_options() -> list[dict[str, str]]:
    table = _character_table()
    return [
        {"id": rank, "label": _word_title(table[rank]["role"])}
        for rank in _ALL_RANKS
        if rank in table and table[rank].get("role")
    ]


def score_for_turn(cards: list[str], *, ace_value: int = 11) -> int:
    values = []
    for card in cards:
        parsed = parse_playing_card(card)
        if parsed:
            values.append(rank_numeric(parsed["rank_key"], ace_as=ace_value))
    return max(values) if values else 0


def format_day_draw(card1: str, card2: str) -> dict[str, Any]:
    adj = lookup_adjective(card1)
    loc = lookup_location_event(card2)
    change = detect_city_change(card1, card2)
    return {
        "card1": card1,
        "card2": card2,
        "adjective": adj,
        "location_event": loc,
        "prompt": f"{adj} {loc}".strip() if adj and loc else "",
        "city_change": change,
    }


def format_character_draw(cards: list[str]) -> dict[str, Any]:
    card1 = cards[0] if cards else ""
    card2 = cards[1] if len(cards) > 1 else ""
    parsed1 = parse_playing_card(card1) if card1 else None
    parsed2 = parse_playing_card(card2) if card2 else None
    trait = lookup_character_trait(parsed1["rank_key"]) if parsed1 else ""
    role = lookup_character_role(parsed2["rank_key"]) if parsed2 else ""
    return {
        "cards": cards,
        "card1": card1,
        "card2": card2,
        "trait": trait,
        "role": role,
        "trait_rank": parsed1["rank_key"] if parsed1 else "",
        "role_rank": parsed2["rank_key"] if parsed2 else "",
        "archetype": format_character_archetype(trait, role),
    }


def format_tables_reference() -> str:
    lines = ["San Sibilia curated tables (from the zine):"]
    char = _character_table()
    lines.append(
        "Character table: first card → trait, second card → role. "
        + ", ".join(
            f"{r}={format_character_archetype(char[r]['trait'], char[r]['role'])}"
            for r in _ALL_RANKS
            if r in char
        )
    )
    lines.append("Adjective table: red suits (hearts/diamonds) vs black suits (clubs/spades) by rank.")
    lines.append("Location/Event table: same red/black split by rank.")
    lines.append("City changes when two drawn cards share suit OR share value.")
    return "\n".join(lines)


def all_ranks_valid() -> bool:
    char = _character_table()
    adj = _adjective_tables()
    loc = _location_tables()
    for rank in _ALL_RANKS:
        if rank not in char or not char[rank].get("trait") or not char[rank].get("role"):
            return False
        if rank not in adj.get("red", {}) or rank not in adj.get("black", {}):
            return False
        if rank not in loc.get("red", {}) or rank not in loc.get("black", {}):
            return False
    return True
