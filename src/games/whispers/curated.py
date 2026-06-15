"""Curated Whispers in the Walls tables (not indexed in Chroma)."""

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
_JOKER_RE = re.compile(r"(?i)^joker\s*\((?P<color>red|black)\)$")
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
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_SUITS = ("hearts", "diamonds", "clubs", "spades")
_RANKS_DECK = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
_SUIT_TABLE = {
    "hearts": "hearts",
    "diamonds": "diamonds",
    "clubs": "clubs",
    "spades": "spades",
}
_SUIT_LABEL = {
    "hearts": "Hearts — The Walls",
    "diamonds": "Diamonds — The Floors",
    "clubs": "Clubs — The Overhead",
    "spades": "Spades — The Hollows",
}


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _locations() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_locations.yaml").get("ranks") or {})


@lru_cache(maxsize=1)
def _hearts() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_hearts.yaml").get("ranks") or {})


@lru_cache(maxsize=1)
def _diamonds() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_diamonds.yaml").get("ranks") or {})


@lru_cache(maxsize=1)
def _clubs() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_clubs.yaml").get("ranks") or {})


@lru_cache(maxsize=1)
def _spades() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_spades.yaml").get("ranks") or {})


@lru_cache(maxsize=1)
def _jokers() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_jokers.yaml") or {})


@lru_cache(maxsize=1)
def _endings() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("whispers_endings.yaml").get("ranks") or {})


@lru_cache(maxsize=1)
def _oracle() -> dict[str, str]:
    return dict(_load_yaml("whispers_oracle.yaml").get("bands") or {})


def parse_playing_card(card: str) -> dict[str, Any] | None:
    raw = card.strip()
    jm = _JOKER_RE.match(raw)
    if jm:
        return {
            "suit": "joker",
            "rank_key": "joker",
            "numeric_value": 0,
            "color": jm.group("color").lower(),
            "card": raw,
            "is_joker": True,
        }
    m = _CARD_RE.match(raw)
    if not m:
        return None
    raw_rank = m.group("rank").lower()
    rank_key = _RANK_ALIASES.get(raw_rank, raw_rank)
    suit = m.group("suit").lower()
    if rank_key == "ace":
        numeric = 1
    elif rank_key in ("jack", "queen", "king"):
        numeric = 10
    else:
        numeric = int(rank_key)
    return {
        "suit": suit,
        "rank_key": rank_key,
        "numeric_value": numeric,
        "card": raw,
        "is_joker": False,
    }


def is_joker_card(card: str) -> bool:
    parsed = parse_playing_card(card)
    return bool(parsed and parsed.get("is_joker"))


def _rank_table(table: dict[str, dict[str, str]], rank_key: str) -> dict[str, str]:
    entry = table.get(rank_key) or {}
    return {
        "body": str(entry.get("body", "")).strip(),
        "title": str(entry.get("title", "")).strip(),
    }


def lookup_location(rank_key: str, *, is_joker: bool = False) -> dict[str, str]:
    key = "joker" if is_joker or rank_key == "joker" else rank_key
    return _rank_table(_locations(), key)


def lookup_suit_prompt(suit: str, rank_key: str) -> dict[str, str]:
    tables = {
        "hearts": _hearts,
        "diamonds": _diamonds,
        "clubs": _clubs,
        "spades": _spades,
    }
    loader = tables.get(suit)
    if not loader:
        return {"body": "", "title": ""}
    return _rank_table(loader(), rank_key)


def lookup_joker_prompt(which: str) -> str:
    entry = _jokers().get(which) or {}
    return str(entry.get("body", "")).strip()


def lookup_ending(rank_key: str, *, is_joker: bool = False) -> str:
    key = "joker" if is_joker or rank_key == "joker" else rank_key
    return _rank_table(_endings(), key)["body"]


def lookup_oracle(total: int) -> str:
    bands = _oracle()
    if total <= 3:
        return bands.get("2-3", "")
    if total <= 6:
        return bands.get("4-6", "")
    if total == 7:
        return bands.get("7", "")
    if total <= 10:
        return bands.get("8-10", "")
    return bands.get("11-12", "")


def build_whispers_deck(*, difficulty: str = "normal", extra_secrets: int = 0) -> list[str]:
    """Construct a shuffled Whispers deck per rules (3 Hollows + 6+ Secrets)."""
    jokers = ["Joker (red)", "Joker (black)"]
    if difficulty == "easy":
        jokers = jokers[:1]
    hollows = list(jokers) + [f"{rank} of spades" for rank in _RANKS_DECK]
    secrets = [f"{rank} of {suit}" for suit in ("hearts", "diamonds", "clubs") for rank in _RANKS_DECK]
    random.shuffle(hollows)
    random.shuffle(secrets)
    picked_hollows = hollows[:3]
    secret_count = min(6 + max(0, extra_secrets), len(secrets))
    picked_secrets = secrets[:secret_count]
    deck = picked_hollows + picked_secrets
    random.shuffle(deck)
    return deck


def format_prompt_block(title: str, body: str) -> str:
    parts = []
    if title.strip():
        parts.append(f"**{title.strip()}**")
    if body.strip():
        parts.append(body.strip())
    return "\n\n".join(parts)


def format_card_draw(
    card: str,
    *,
    jokers_drawn_before: int = 0,
    is_final_card: bool = False,
    is_location: bool = False,
) -> dict[str, Any]:
    """Resolve a card to table text. PDF p.7–33."""
    parsed = parse_playing_card(card)
    if not parsed:
        return {
            "card": card,
            "table": "",
            "title": "",
            "prompt": "",
            "is_joker": False,
            "joker_slot": None,
            "trigger_joker_ending": False,
            "ending": "",
            "is_final": is_final_card,
        }

    if parsed.get("is_joker"):
        slot = "first" if jokers_drawn_before < 1 else "second"
        body = lookup_joker_prompt(slot)
        title = "Jokers — The Dead" if slot == "first" else "Jokers — The Dead (second)"
        trigger = slot == "second"
        ending = ""
        if trigger:
            ending = lookup_ending("joker", is_joker=True)
        elif is_final_card:
            rank_key = "joker"
            ending = lookup_ending(rank_key, is_joker=True)
        return {
            "card": card,
            "table": "jokers",
            "title": title,
            "prompt": format_prompt_block(title, body),
            "is_joker": True,
            "joker_slot": slot,
            "trigger_joker_ending": trigger,
            "ending": ending,
            "is_final": is_final_card,
        }

    rank_key = str(parsed["rank_key"])
    suit = str(parsed["suit"])

    if is_location:
        loc = lookup_location(rank_key)
        title = loc["title"] or "Location"
        prompt = format_prompt_block(title, loc["body"])
        return {
            "card": card,
            "table": "locations",
            "title": title,
            "prompt": prompt,
            "is_joker": False,
            "joker_slot": None,
            "trigger_joker_ending": False,
            "ending": "",
            "is_final": False,
        }

    suit_entry = lookup_suit_prompt(suit, rank_key)
    table_name = _SUIT_TABLE[suit]
    title = _SUIT_LABEL.get(suit, suit)
    prompt = format_prompt_block(title, suit_entry["body"])
    ending = lookup_ending(rank_key) if is_final_card else ""
    if is_final_card and ending:
        prompt += f"\n\n**The Ending**\n\n{ending}"
    return {
        "card": card,
        "table": table_name,
        "title": title,
        "prompt": prompt,
        "is_joker": False,
        "joker_slot": None,
        "trigger_joker_ending": False,
        "ending": ending,
        "is_final": is_final_card,
    }


def all_ranks_valid() -> bool:
    for table in (_hearts(), _diamonds(), _clubs(), _spades(), _locations(), _endings()):
        for rank in _ALL_RANKS:
            if rank not in table:
                return False
            if not str(table[rank].get("body", "")).strip():
                return False
    if "joker" not in _locations():
        return False
    for key in ("first", "second", "all_revealed"):
        if not lookup_joker_prompt(key):
            return False
    if not lookup_ending("joker", is_joker=True):
        return False
    return True
