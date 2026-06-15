"""Curated Colostle card tables (not indexed in Chroma)."""

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
_RED_SUITS = frozenset({"hearts", "diamonds"})
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_NUMERIC = {"ace": 1, **{str(n): n for n in range(2, 11)}, "jack": 11, "queen": 12, "king": 13}


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


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
        "numeric_value": _NUMERIC.get(rank_key, 0),
        "color": color,
        "card": card.strip(),
        "is_red": color == "red",
    }


def _rank_band(rank_key: str) -> str:
    n = _NUMERIC.get(rank_key, 0)
    if n <= 2:
        return "ace_2"
    if n <= 4:
        return "3_4"
    if n <= 6:
        return "5_6"
    if n <= 8:
        return "7_8"
    if n <= 10:
        return "9_10"
    if rank_key in ("jack", "queen"):
        return "jack_queen"
    return "king"


def _oracle_band(rank_key: str) -> str:
    n = _NUMERIC.get(rank_key, 0)
    if n <= 4:
        return "ace_4"
    if n <= 9:
        return "5_9"
    return "10_k"


def _high_low(rank_key: str) -> str:
    return "high" if _NUMERIC.get(rank_key, 0) >= 7 else "low"


def _guild_location_band(rank_key: str) -> str:
    n = _NUMERIC.get(rank_key, 0)
    if n <= 2:
        return "ace_2"
    if n == 3:
        return "3"
    if n <= 5:
        return "4_5"
    if n == 6:
        return "6"
    if n <= 8:
        return "7_8"
    if n == 9:
        return "9"
    if rank_key in ("10", "jack"):
        return "10_j"
    if rank_key == "queen":
        return "queen"
    return "king"


@lru_cache(maxsize=1)
def _classes() -> dict[str, Any]:
    return _load_yaml("colostle_classes.yaml")


@lru_cache(maxsize=1)
def _calling() -> dict[str, Any]:
    return _load_yaml("colostle_calling.yaml")


@lru_cache(maxsize=1)
def _nature() -> dict[str, Any]:
    return _load_yaml("colostle_nature.yaml")


@lru_cache(maxsize=1)
def _roomlands_red() -> dict[str, Any]:
    return _load_yaml("colostle_roomlands_red.yaml")


@lru_cache(maxsize=1)
def _roomlands_black() -> dict[str, Any]:
    return _load_yaml("colostle_roomlands_black.yaml")


@lru_cache(maxsize=1)
def _items() -> dict[str, Any]:
    return _load_yaml("colostle_items.yaml")


@lru_cache(maxsize=1)
def _events() -> dict[str, Any]:
    return _load_yaml("colostle_events.yaml")


@lru_cache(maxsize=1)
def _faces() -> dict[str, Any]:
    return _load_yaml("colostle_exploration_faces.yaml")


@lru_cache(maxsize=1)
def _oracle() -> dict[str, Any]:
    return _load_yaml("colostle_oracle.yaml")


@lru_cache(maxsize=1)
def _storytelling() -> dict[str, Any]:
    return _load_yaml("colostle_storytelling.yaml")


@lru_cache(maxsize=1)
def _npc() -> dict[str, Any]:
    return _load_yaml("colostle_npc.yaml")


@lru_cache(maxsize=1)
def _ocean() -> dict[str, Any]:
    return _load_yaml("colostle_ocean.yaml")


@lru_cache(maxsize=1)
def _ocean_weather() -> dict[str, Any]:
    return _load_yaml("colostle_ocean_weather.yaml")


@lru_cache(maxsize=1)
def _city() -> dict[str, Any]:
    return _load_yaml("colostle_city.yaml")


@lru_cache(maxsize=1)
def _hunters_guild() -> dict[str, Any]:
    return _load_yaml("colostle_hunters_guild.yaml")


@lru_cache(maxsize=1)
def _rookling() -> dict[str, Any]:
    return _load_yaml("colostle_rookling.yaml")


@lru_cache(maxsize=1)
def _battlements() -> dict[str, Any]:
    return _load_yaml("colostle_battlements.yaml")


@lru_cache(maxsize=1)
def _exposure() -> dict[str, Any]:
    return _load_yaml("colostle_exposure.yaml")


@lru_cache(maxsize=1)
def _combat() -> dict[str, Any]:
    return _load_yaml("colostle_combat.yaml")


def class_options() -> list[dict[str, Any]]:
    classes = (_classes().get("classes") or {})
    return [
        {
            "id": cid,
            "label": str(data.get("label", cid)),
            "exploration": int(data.get("exploration", 0)),
            "combat": int(data.get("combat", 0)),
        }
        for cid, data in classes.items()
        if isinstance(data, dict)
    ]


def lookup_class(class_id: str) -> dict[str, Any]:
    data = (_classes().get("classes") or {}).get(class_id) or {}
    return {
        "id": class_id,
        "label": str(data.get("label", class_id)),
        "exploration": int(data.get("exploration", 0)),
        "combat": int(data.get("combat", 0)),
    }


def lookup_calling(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    band = _rank_band(parsed["rank_key"])
    return str((_calling().get("bands") or {}).get(band, ""))


def lookup_nature(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    band = _rank_band(parsed["rank_key"])
    return str((_nature().get("bands") or {}).get(band, ""))


def lookup_item(rank_key: str) -> str:
    return str((_items().get("ranks") or {}).get(rank_key, ""))


def lookup_event(rank_key: str) -> str:
    return str((_events().get("ranks") or {}).get(rank_key, ""))


def lookup_exploration_face(rank_key: str) -> str:
    return str((_faces().get("faces") or {}).get(rank_key, ""))


def lookup_roomlands(card: str) -> dict[str, str]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "prompt": "", "table": ""}
    rk = parsed["rank_key"]
    if rk in ("jack", "queen", "king"):
        prompt = lookup_exploration_face(rk)
        return {"card": card, "prompt": prompt, "table": "face", "rank_key": rk}
    if parsed["is_red"]:
        row = (_roomlands_red().get("ranks") or {}).get(rk) or {}
        suit_key = parsed["suit"]
        prompt = str(row.get(suit_key, ""))
        return {"card": card, "prompt": prompt, "table": "roomlands_red", "suit": suit_key}
    row = (_roomlands_black().get("ranks") or {}).get(rk) or {}
    suit_key = parsed["suit"]
    prompt = str(row.get(suit_key, ""))
    return {"card": card, "prompt": prompt, "table": "roomlands_black", "suit": suit_key}


def lookup_oracle(card: str) -> dict[str, str]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "answer": ""}
    band = _oracle_band(parsed["rank_key"])
    row = (_oracle().get("bands") or {}).get(band) or {}
    color = parsed["color"]
    return {
        "card": card,
        "color": color,
        "band": band,
        "answer": str(row.get(color, "")),
    }


def lookup_storytelling(card: str) -> dict[str, str]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "incite": "", "subject": "", "twist": ""}
    row = (_storytelling().get("ranks") or {}).get(parsed["rank_key"]) or {}
    return {
        "card": card,
        "incite": str(row.get("incite", "")),
        "subject": str(row.get("subject", "")),
        "twist": str(row.get("twist", "")),
    }


def lookup_npc(card: str) -> dict[str, str]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "name": "", "look": "", "trait": ""}
    row = (_npc().get("ranks") or {}).get(parsed["rank_key"]) or {}
    return {
        "card": card,
        "name": str(row.get("name", "")),
        "look": str(row.get("look", "")),
        "trait": str(row.get("trait", "")),
    }


def lookup_ocean(card: str) -> dict[str, str]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "prompt": ""}
    rk = parsed["rank_key"]
    if rk in ("jack", "queen", "king"):
        prompt = str((_ocean().get("ranks") or {}).get(rk, ""))
        return {"card": card, "prompt": prompt, "table": "ocean_face"}
    row = (_ocean().get("ranks") or {}).get(rk) or {}
    color = parsed["color"]
    prompt = str(row.get(color, ""))
    return {"card": card, "prompt": prompt, "table": "ocean", "color": color}


def lookup_ocean_weather(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    return str((_ocean_weather().get("ranks") or {}).get(parsed["rank_key"], ""))


def lookup_city(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    return str((_city().get("ranks") or {}).get(parsed["rank_key"], ""))


def lookup_hunters_guild(cards: list[str]) -> dict[str, str]:
    if len(cards) < 4:
        return {"error": "Need 4 cards: distance, location, twist, reward"}
    parsed = [parse_playing_card(c) for c in cards]
    if not all(parsed):
        return {"error": "Invalid card format"}
    distance = str(
        ((_hunters_guild().get("distance_by_suit") or {}).get(parsed[0]["suit"], ""))
    )
    loc_band = _guild_location_band(parsed[1]["rank_key"])
    location = str(((_hunters_guild().get("location") or {}).get(loc_band, "")))
    twist = str(((_hunters_guild().get("twist") or {}).get(parsed[2]["rank_key"], "")))
    reward = str(
        ((_hunters_guild().get("reward_by_suit") or {}).get(parsed[3]["suit"], ""))
    )
    return {
        "distance": distance,
        "location": location,
        "twist": twist,
        "reward": reward,
        "cards": ", ".join(cards),
    }


def lookup_rookling(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    return str((_rookling().get("ranks") or {}).get(parsed["rank_key"], ""))


def lookup_battlements(card: str) -> dict[str, str]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "prompt": ""}
    rk = parsed["rank_key"]
    if rk in ("jack", "queen", "king"):
        prompt = str((_battlements().get("ranks") or {}).get(rk, ""))
        return {"card": card, "prompt": prompt, "table": "battlements_face"}
    row = (_battlements().get("ranks") or {}).get(rk) or {}
    color = parsed["color"]
    prompt = str(row.get(color, ""))
    return {"card": card, "prompt": prompt, "table": "battlements", "color": color}


def lookup_exposure(card: str) -> str:
    parsed = parse_playing_card(card)
    if not parsed:
        return ""
    rk = parsed["rank_key"]
    if rk in ("jack", "queen", "king"):
        return str((_exposure().get("bands") or {}).get("jack_queen_king", ""))
    return str((_exposure().get("bands") or {}).get(_rank_band(rk), ""))


def lookup_combat_attack(suit: str) -> str:
    return str((_combat().get("attack_by_suit") or {}).get(suit.lower(), ""))


def format_person_opponent(intention_card: str, weapon_card: str) -> dict[str, str]:
    pi = parse_playing_card(intention_card)
    pw = parse_playing_card(weapon_card)
    intention = lookup_combat_attack(pi["suit"]) if pi else ""
    if pi:
        row = (_combat().get("person_intention") or {})
        intention = str(row.get(pi["suit"], ""))
    weapon = ""
    if pw:
        wl = _high_low(pw["rank_key"])
        weapon = str((_combat().get("weapon_by_rank") or {}).get(wl, ""))
    return {
        "intention_card": intention_card,
        "weapon_card": weapon_card,
        "intention": intention,
        "weapon_type": weapon,
        "combat_score": str((_combat().get("opponent_combat_score") or {}).get("person", 1)),
    }


def format_rook_opponent(
    body_card: str,
    magic_card: str,
    weapon_card: str,
    reward_card: str,
) -> dict[str, str]:
    pb, pm, pw, pr = (
        parse_playing_card(body_card),
        parse_playing_card(magic_card),
        parse_playing_card(weapon_card),
        parse_playing_card(reward_card),
    )
    body = ""
    if pb:
        body = str((_combat().get("rook_body") or {}).get(_high_low(pb["rank_key"]), ""))
    magic = str(((_combat().get("rook_magic") or {}).get(pm["suit"], ""))) if pm else ""
    weapon = ""
    if pw:
        weapon = str((_combat().get("weapon_by_rank") or {}).get(_high_low(pw["rank_key"]), ""))
    reward = str(((_combat().get("rook_reward") or {}).get(pr["suit"], ""))) if pr else ""
    return {
        "body_card": body_card,
        "magic_card": magic_card,
        "weapon_card": weapon_card,
        "reward_card": reward_card,
        "body_type": body,
        "magic_type": magic,
        "weapon_type": weapon,
        "reward": reward,
    }


def format_exploration_draw(cards: list[str]) -> list[dict[str, str]]:
    return [lookup_roomlands(c) for c in cards]


def format_character_draw(calling_card: str, nature_card: str) -> dict[str, str]:
    return {
        "calling_card": calling_card,
        "nature_card": nature_card,
        "calling": lookup_calling(calling_card),
        "nature": lookup_nature(nature_card),
    }


def all_ranks_valid() -> bool:
    checks = [
        (_items().get("ranks") or {}),
        (_events().get("ranks") or {}),
        (_ocean_weather().get("ranks") or {}),
        (_rookling().get("ranks") or {}),
    ]
    return all(all(r in table for r in _ALL_RANKS) for table in checks)


def all_roomlands_ranks_valid() -> bool:
    red = (_roomlands_red().get("ranks") or {})
    black = (_roomlands_black().get("ranks") or {})
    for rk in ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10"):
        if rk not in red or rk not in black:
            return False
    return True
