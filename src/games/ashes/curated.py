"""Curated Ashes card tables (not indexed in Chroma)."""

from __future__ import annotations

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
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_RED_SUITS = frozenset({"hearts", "diamonds"})
_BLACK_SUITS = frozenset({"clubs", "spades"})
_SUIT_LABELS = {
    "hearts": "Hearts",
    "diamonds": "Diamonds",
    "clubs": "Clubs",
    "spades": "Spades",
}


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _room_table() -> dict[str, dict[str, str]]:
    raw = _load_yaml("ashes_room_table.yaml").get("ranks") or {}
    return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}


@lru_cache(maxsize=1)
def _enemy_table() -> dict[str, str]:
    raw = _load_yaml("ashes_enemy_table.yaml").get("ranks") or {}
    return {str(k): str(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def _suit_features() -> dict[str, dict[str, str]]:
    raw = _load_yaml("ashes_suit_features.yaml").get("suits") or {}
    return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}


@lru_cache(maxsize=1)
def _failure_consequences() -> dict[str, dict[str, str]]:
    raw = _load_yaml("ashes_failure_consequences.yaml").get("rooms") or {}
    return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}


@lru_cache(maxsize=1)
def _trap_table() -> dict[str, str]:
    raw = _load_yaml("ashes_trap_table.yaml").get("rolls") or {}
    return {str(k): str(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def _fates_gift() -> dict[str, str]:
    raw = _load_yaml("ashes_fates_gift.yaml").get("ranks") or {}
    return {str(k): str(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def _armour_table() -> dict[str, str]:
    raw = _load_yaml("ashes_armour.yaml").get("rolls") or {}
    return {str(k): str(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def _loot_table() -> dict[str, str]:
    raw = _load_yaml("ashes_loot_table.yaml").get("rolls") or {}
    return {str(k): str(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def _journal_sets() -> dict[str, dict[str, dict[str, dict[str, str]]]]:
    data = _load_yaml("ashes_journal_prompts.yaml")
    sets = data.get("sets") or {}
    out: dict[str, dict[str, dict[str, dict[str, str]]]] = {}
    for set_id, block in sets.items():
        if not isinstance(block, dict):
            continue
        out[str(set_id)] = {}
        for suit in ("hearts", "diamonds", "clubs", "spades"):
            rows = block.get(suit) or {}
            out[str(set_id)][suit] = {str(k): dict(v) for k, v in rows.items() if isinstance(v, dict)}
    return out


@lru_cache(maxsize=1)
def _journal_default_set() -> str:
    data = _load_yaml("ashes_journal_prompts.yaml")
    return str(data.get("default_set") or "crypt")


@lru_cache(maxsize=1)
def _trials() -> dict[str, dict[str, str]]:
    raw = _load_yaml("ashes_trials.yaml")
    return {
        "red": {str(k): str(v) for k, v in (raw.get("red") or {}).items()},
        "black": {str(k): str(v) for k, v in (raw.get("black") or {}).items()},
    }


@lru_cache(maxsize=1)
def _ember_levels() -> dict[str, int]:
    raw = _load_yaml("ashes_ember_levels.yaml").get("levels") or {}
    return {str(k): int(v) for k, v in raw.items()}


@lru_cache(maxsize=1)
def _starting_weapons() -> dict[str, dict[str, str]]:
    raw = _load_yaml("ashes_starting_weapons.yaml")
    out: dict[str, dict[str, str]] = {}
    for kind in ("melee", "ranged"):
        block = raw.get(kind) or {}
        out[kind] = {str(k): str(v) for k, v in block.items()}
    return out


@lru_cache(maxsize=1)
def _classes() -> dict[str, dict[str, Any]]:
    raw = _load_yaml("ashes_classes.yaml").get("classes") or {}
    return {str(k): dict(v) for k, v in raw.items() if isinstance(v, dict)}


def parse_playing_card(card: str) -> dict[str, Any] | None:
    m = _CARD_RE.match(card.strip())
    if not m:
        return None
    raw_rank = m.group("rank").lower()
    rank_key = _RANK_ALIASES.get(raw_rank, raw_rank)
    suit = m.group("suit").lower()
    if rank_key == "ace":
        numeric = 1
    elif rank_key in ("jack", "queen", "king"):
        numeric = 11
    else:
        numeric = int(rank_key)
    return {
        "suit": suit,
        "suit_label": _SUIT_LABELS.get(suit, suit.title()),
        "rank_key": rank_key,
        "numeric_value": numeric,
        "card": card.strip(),
    }


def lookup_room(rank_key: str) -> dict[str, str]:
    return dict(_room_table().get(rank_key, {}))


def lookup_enemy(rank_key: str) -> str:
    return _enemy_table().get(rank_key, "")


def lookup_suit_feature(suit: str) -> dict[str, str]:
    return dict(_suit_features().get(suit.lower(), {}))


def lookup_failure(room_name: str) -> dict[str, str]:
    key = room_name.strip()
    table = _failure_consequences()
    if key in table:
        return dict(table[key])
    for name, row in table.items():
        if name.lower() in key.lower() or key.lower() in name.lower():
            return dict(row)
    return {}


def lookup_trap(roll: int) -> str:
    return _trap_table().get(str(roll), "")


def lookup_fates_gift(rank_key: str) -> str:
    return _fates_gift().get(rank_key, "")


def lookup_armour(roll: int) -> str:
    return _armour_table().get(str(roll), "")


def lookup_loot(roll: int) -> str:
    return _loot_table().get(str(roll), "")


def lookup_journal_prompt(suit: str, rank_key: str, *, prompt_set: str | None = None) -> dict[str, str]:
    set_id = prompt_set or _journal_default_set()
    block = _journal_sets().get(set_id) or _journal_sets().get(_journal_default_set(), {})
    return dict(block.get(suit.lower(), {}).get(rank_key, {}))


def prompt_set_options() -> list[dict[str, str]]:
    data = _load_yaml("ashes_journal_prompts.yaml")
    labels = data.get("labels") or {}
    sets = _journal_sets()
    return [
        {"id": sid, "label": str(labels.get(sid) or sid.replace("_", " ").title())}
        for sid in sets
    ]


def trial_color(suit: str) -> str:
    return "red" if suit.lower() in _RED_SUITS else "black"


def lookup_trial(rank_key: str, color: str) -> str:
    return _trials().get(color, {}).get(rank_key, "")


def ember_for_level(level: int) -> int:
    return _ember_levels().get(str(level), 1 + 2 * level)


def lookup_starting_weapon(kind: str, roll: int) -> str:
    table = _starting_weapons().get(kind, {})
    key = str(roll)
    if key in table:
        return table[key]
    return table.get(str(min(6, max(1, roll))), "")


def class_options() -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for cid, row in _classes().items():
        out.append({"id": cid, "label": str(row.get("label") or cid.title())})
    return out


def format_room_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    rank_key = parsed["rank_key"]
    suit = parsed["suit"]
    room = lookup_room(rank_key)
    feature = lookup_suit_feature(suit)
    room_name = str(room.get("room") or "")
    failure = lookup_failure(room_name) if room_name else {}
    return {
        "card": card,
        "rank_key": rank_key,
        "suit": suit,
        "suit_label": parsed["suit_label"],
        "room": room_name,
        "check": str(room.get("check") or ""),
        "suit_feature": str(feature.get("feature") or ""),
        "suit_detail": str(feature.get("detail") or ""),
        "suit_check": feature.get("check"),
        "failure": failure,
        "spades_extra_enemy": suit == "spades" and "COMBAT" in str(room.get("check") or "").upper(),
    }


def format_journal_draw(card: str, *, prompt_set: str | None = None) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    prompt = lookup_journal_prompt(parsed["suit"], parsed["rank_key"], prompt_set=prompt_set)
    set_id = prompt_set or _journal_default_set()
    suit_note = ""
    if parsed["suit"] == "diamonds":
        suit_note = "Roll INT; if you pass, roll for loot."
    elif parsed["suit"] == "spades":
        suit_note = "Roll INT; roll for loot on a pass."
    return {
        "card": card,
        "suit": parsed["suit"],
        "suit_label": parsed["suit_label"],
        "rank_key": parsed["rank_key"],
        "event": str(prompt.get("event") or ""),
        "check": str(prompt.get("check") or ""),
        "suit_note": suit_note,
        "prompt_set": set_id,
        "prompt": f"{prompt.get('event', '')} ({prompt.get('check', '')})".strip(),
    }


def format_trial_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    color = trial_color(parsed["suit"])
    trial = lookup_trial(parsed["rank_key"], color)
    return {
        "card": card,
        "rank_key": parsed["rank_key"],
        "suit": parsed["suit"],
        "color": color,
        "trial": trial,
    }


def format_trials_draw(cards: list[str]) -> dict[str, Any]:
    trials = [format_trial_draw(c) for c in cards]
    return {"cards": cards, "trials": trials}


def format_enemy_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    enemy = lookup_enemy(parsed["rank_key"])
    return {
        "card": card,
        "rank_key": parsed["rank_key"],
        "enemy": enemy,
    }


def format_character_gift_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    gift = lookup_fates_gift(parsed["rank_key"])
    return {
        "card": card,
        "rank_key": parsed["rank_key"],
        "gift": gift,
    }


def all_ranks_valid() -> bool:
    room = _room_table()
    enemy = _enemy_table()
    gift = _fates_gift()
    for rank in _ALL_RANKS:
        if rank not in room or rank not in enemy or rank not in gift:
            return False
    sets = _journal_sets()
    default = _journal_default_set()
    for set_id, block in sets.items():
        for suit in ("hearts", "diamonds", "clubs", "spades"):
            for rank in _ALL_RANKS:
                if rank not in block.get(suit, {}):
                    return False
    trials = _trials()
    for color in ("red", "black"):
        for rank in _ALL_RANKS:
            if rank not in trials.get(color, {}):
                return False
    _ = default
    return True
