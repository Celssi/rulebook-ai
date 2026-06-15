"""Curated Apothecaria tables (not indexed in Chroma)."""

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
_AILMENT_RANKS = ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_FAMILIAR_RANK_KEYS = {
    "ace": "ace",
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
    "jack": "jack",
    "queen": "queen",
    "king": "king",
}
_LOCALE_LABELS = {
    "village": "The Village",
    "glimmerwood": "Glimmerwood Grove",
    "blastfire_bog": "Blastfire Bog",
    "meltwater_loch": "Meltwater Loch",
    "dreamwater_depths": "Dreamwater Depths",
    "moonbreaker_mountain": "Moonbreaker Mountain",
    "cloud_isles": "The Cloud Isles",
    "heros_hollow": "Hero's Hollow",
    "the_strange": "The Strange",
}
_REAGENT_LOCALE_KEYS = {
    "forest": "glimmerwood",
    "bog": "blastfire_bog",
    "loch": "meltwater_loch",
    "depths": "dreamwater_depths",
    "mountain": "moonbreaker_mountain",
    "isles": "cloud_isles",
    "strange": "the_strange",
    "dungeon": "heros_hollow",
    "village": "village",
}
_SILVER_BASE = {"novice": 15, "intermediate": 25, "advanced": 35, "expert": 50}


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _ailments() -> dict[str, dict[str, dict]]:
    return dict(_load_yaml("apothecaria_ailments.yaml").get("tiers") or {})


@lru_cache(maxsize=1)
def _locale_events() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("apothecaria_locale_events.yaml").get("locales") or {})


@lru_cache(maxsize=1)
def _patient_types() -> dict[str, str]:
    return dict(_load_yaml("apothecaria_patient_types.yaml").get("suits") or {})


@lru_cache(maxsize=1)
def _familiars() -> dict[str, Any]:
    return _load_yaml("apothecaria_familiars.yaml")


@lru_cache(maxsize=1)
def _reagents() -> list[dict[str, Any]]:
    raw = _load_yaml("apothecaria_reagents.yaml").get("reagents") or []
    return list(raw) if isinstance(raw, list) else []


@lru_cache(maxsize=1)
def _tools() -> dict[str, Any]:
    return _load_yaml("apothecaria_tools.yaml")


@lru_cache(maxsize=1)
def _upgrades() -> list[dict[str, Any]]:
    raw = _load_yaml("apothecaria_upgrades.yaml").get("upgrades") or []
    return list(raw) if isinstance(raw, list) else []


@lru_cache(maxsize=1)
def _village() -> list[dict[str, Any]]:
    raw = _load_yaml("apothecaria_village.yaml").get("services") or []
    return list(raw) if isinstance(raw, list) else []


@lru_cache(maxsize=1)
def _festivals() -> dict[str, Any]:
    return dict(_load_yaml("apothecaria_festivals.yaml").get("festivals") or {})


@lru_cache(maxsize=1)
def _witch_storyline() -> dict[str, dict[str, str]]:
    return dict(_load_yaml("apothecaria_witch_storyline.yaml").get("tables") or {})


@lru_cache(maxsize=1)
def _locale_meta() -> dict[str, Any]:
    return dict(_load_yaml("apothecaria_locale_events.yaml").get("meta") or {})


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
        numeric = {"jack": 11, "queen": 12, "king": 13}[rank_key]
    else:
        numeric = int(rank_key)
    return {
        "suit": suit,
        "rank_key": rank_key,
        "numeric_value": numeric,
        "card": card.strip(),
    }


def rank_numeric(rank_key: str) -> int:
    if rank_key == "ace":
        return 1
    if rank_key == "jack":
        return 11
    if rank_key == "queen":
        return 12
    if rank_key == "king":
        return 13
    return int(rank_key)


def reputation_tier(reputation: int) -> str:
    rep = max(0, int(reputation))
    if rep >= 33:
        return "expert"
    if rep >= 22:
        return "advanced"
    if rep >= 11:
        return "intermediate"
    return "novice"


def reputation_tier_label(reputation: int) -> str:
    return reputation_tier(reputation).title()


def silver_base_rate(reputation: int) -> int:
    return _SILVER_BASE[reputation_tier(reputation)]


def normalize_reagent_locales(locales: dict[str, Any]) -> dict[str, int]:
    out: dict[str, int] = {}
    for key, value in locales.items():
        loc = _REAGENT_LOCALE_KEYS.get(str(key), str(key))
        out[loc] = int(value)
    return out


def lookup_reagent(name: str) -> dict[str, Any] | None:
    needle = name.strip().lower()
    for reg in _reagents():
        if str(reg.get("name", "")).strip().lower() == needle:
            entry = dict(reg)
            entry["locales"] = normalize_reagent_locales(reg.get("locales") or {})
            return entry
    return None


def reagents_for_tags(tags: list[str], limit: int = 12) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for tag in tags:
        for reg in reagents_matching_tag(tag, limit=limit):
            name = str(reg.get("name", ""))
            if name in seen:
                continue
            seen.add(name)
            entry = dict(reg)
            entry["locales"] = normalize_reagent_locales(reg.get("locales") or {})
            out.append(entry)
            if len(out) >= limit:
                return out
    return out


def all_purchasable_tools() -> list[dict[str, Any]]:
    return list((_tools().get("purchasable") or []))


def lookup_purchasable_tool(tool_id: str) -> dict[str, Any] | None:
    for tool in all_purchasable_tools():
        if str(tool.get("id", "")) == tool_id:
            return tool
    return None


def all_upgrades() -> list[dict[str, Any]]:
    return list(_upgrades())


def lookup_upgrade(upgrade_id: str) -> dict[str, Any] | None:
    for up in all_upgrades():
        if str(up.get("id", "")) == upgrade_id:
            return up
    return None


def village_services() -> list[dict[str, Any]]:
    return list(_village())


def festival_for_season(season: str) -> dict[str, Any]:
    return dict(_festivals().get(season.lower(), {}))


def witch_storyline_tables() -> list[str]:
    return list(_witch_storyline().keys())


def lookup_witch_clue(table: str, rank_key: str) -> str:
    tables = _witch_storyline()
    rows = tables.get(table) or {}
    key = "ace" if rank_key == "ace" else rank_key
    return str(rows.get(key, ""))


def locale_meta() -> dict[str, Any]:
    return dict(_locale_meta())


def lookup_ailment(reputation: int, rank_key: str) -> dict[str, Any]:
    tier = reputation_tier(reputation)
    tiers = _ailments()
    lookup_rank = "1" if rank_key == "ace" else rank_key
    entry = (tiers.get(tier) or {}).get(lookup_rank) or {}
    if not entry:
        for lower in ("novice", "intermediate", "advanced", "expert"):
            if lower in tiers and rank_key in tiers[lower]:
                entry = tiers[lower][rank_key]
                break
    if not isinstance(entry, dict):
        return {}
    tags = entry.get("tags") or []
    name = str(entry.get("name", ""))
    consequence = str(entry.get("consequence", "") or "").strip()
    description = _clean_ailment_description(
        str(entry.get("description", "")),
        name=name,
        tags=[str(t) for t in tags],
        consequence=consequence,
    )
    return {
        "name": name,
        "tags": [str(t) for t in tags],
        "timer": entry.get("timer"),
        "description": description,
        "consequence": consequence,
        "tier": tier,
        "rank": rank_key,
    }


def _clean_ailment_description(
    description: str,
    *,
    name: str = "",
    tags: list[str] | None = None,
    consequence: str = "",
) -> str:
    text = description.strip()
    if not text:
        return ""
    if name and text.lower().startswith(name.lower()):
        text = text[len(name) :].lstrip(" -–—:")
    for tag in tags or []:
        text = re.sub(rf"\[\s*{re.escape(tag)}\s*\]", "", text, flags=re.I)
    text = re.sub(r"Timer:\s*\d+", "", text, flags=re.I)
    text = re.sub(r"Consequence:\s*", "", text, flags=re.I)
    if consequence:
        tail = consequence.rstrip(".")
        if text.rstrip(".").endswith(tail):
            text = text[: -len(tail)].rstrip(" .")
    text = re.sub(r"^[-–—]\s*", "", text)
    return re.sub(r"\s{2,}", " ", text).strip()


def lookup_patient_type(suit: str) -> str:
    return str(_patient_types().get(suit.lower(), ""))


def lookup_locale_event(locale: str, rank_key: str) -> str:
    loc = locale.lower().strip()
    events = (_locale_events().get(loc) or {})
    key = "ace" if rank_key == "ace" else rank_key
    return str(events.get(key, ""))


def lookup_familiar_type(rank_key: str) -> str:
    key = _FAMILIAR_RANK_KEYS.get(rank_key, rank_key)
    return str((_familiars().get("types") or {}).get(key, ""))


def lookup_familiar_skill(rank_key: str) -> str:
    key = _FAMILIAR_RANK_KEYS.get(rank_key, rank_key)
    return str((_familiars().get("skills") or {}).get(key, ""))


def locale_options() -> list[dict[str, str]]:
    return [{"id": lid, "label": _LOCALE_LABELS.get(lid, lid.replace("_", " ").title())} for lid in _LOCALE_LABELS]


def format_ailment_draw(card: str, reputation: int) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    ailment = lookup_ailment(reputation, parsed["rank_key"])
    tags = ", ".join(f"[{t}]" for t in ailment.get("tags") or [])
    timer = ailment.get("timer")
    timer_str = f" — Timer: {timer}" if timer is not None else ""
    summary = f"**{ailment.get('name', '?')}** {tags}{timer_str}"
    return {
        "card": card,
        "rank": parsed["rank_key"],
        "tier": ailment.get("tier", reputation_tier(reputation)),
        "name": ailment.get("name", ""),
        "tags": ailment.get("tags") or [],
        "timer": timer,
        "description": ailment.get("description", ""),
        "consequence": ailment.get("consequence", ""),
        "summary": summary,
    }


def format_patient_type_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    ptype = lookup_patient_type(parsed["suit"])
    return {
        "card": card,
        "suit": parsed["suit"],
        "patient_type": ptype,
        "summary": f"**{ptype}** ({parsed['suit']})",
    }


def format_forage_draw(card: str, locale: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "locale": locale, "error": "Could not parse card"}
    event = lookup_locale_event(locale, parsed["rank_key"])
    label = _LOCALE_LABELS.get(locale, locale)
    return {
        "card": card,
        "rank": parsed["rank_key"],
        "numeric_value": parsed["numeric_value"],
        "locale": locale,
        "locale_label": label,
        "event": event,
        "summary": f"**{label}** — {card} (value {parsed['numeric_value']})",
    }


def format_familiar_type_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    ftype = lookup_familiar_type(parsed["rank_key"])
    return {"card": card, "rank": parsed["rank_key"], "familiar_type": ftype, "summary": f"**{ftype}**"}


def format_familiar_skill_draw(card: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    skill = lookup_familiar_skill(parsed["rank_key"])
    return {"card": card, "rank": parsed["rank_key"], "familiar_skill": skill, "summary": f"**{skill}**"}


def reagents_matching_tag(tag: str, limit: int = 8) -> list[dict[str, Any]]:
    needle = tag.strip().upper()
    out: list[dict[str, Any]] = []
    for reg in _reagents():
        tags = [str(t).upper() for t in (reg.get("tags") or [])]
        if needle in tags:
            entry = dict(reg)
            entry["locales"] = normalize_reagent_locales(reg.get("locales") or {})
            out.append(entry)
        if len(out) >= limit:
            break
    return out


def foraging_rules_text() -> str:
    return (
        "**Foraging**\n\n"
        "1. Note Foraging points (start at 0 for each locale track).\n"
        "2. Draw a card and resolve the locale event.\n"
        "3. If card value ≥ reagent Foraging Value, you found it (one at a time).\n"
        "4. If lower, gain 1 Foraging point (2 with Sickle).\n"
        "5. When points ≥ reagent value, you automatically find the reagent.\n"
        "6. If the ailment has a Timer, decrease it by 1 after each event or locale shift."
    )


def format_witch_clue_draw(card: str, table: str) -> dict[str, Any]:
    parsed = parse_playing_card(card)
    if not parsed:
        return {"card": card, "error": "Could not parse card"}
    clue = lookup_witch_clue(table, parsed["rank_key"])
    return {
        "card": card,
        "rank": parsed["rank_key"],
        "table": table,
        "clue": clue,
        "summary": f"**{table.replace('_', ' ').title()}** — {clue}",
    }


def all_ranks_valid() -> bool:
    ailments = _ailments()
    for tier, rows in ailments.items():
        if not isinstance(rows, dict):
            return False
        for rank in _AILMENT_RANKS:
            if rank not in rows:
                raise AssertionError(f"Missing ailment rank {rank!r} in tier {tier!r}")
    fam = _familiars()
    for rank in _FAMILIAR_RANK_KEYS.values():
        if rank not in (fam.get("types") or {}):
            raise AssertionError(f"Missing familiar type for rank {rank!r}")
        if rank not in (fam.get("skills") or {}):
            raise AssertionError(f"Missing familiar skill for rank {rank!r}")
    for suit in ("hearts", "diamonds", "clubs", "spades"):
        if suit not in _patient_types():
            raise AssertionError(f"Missing patient type for suit {suit!r}")
    for loc, events in _locale_events().items():
        if not isinstance(events, dict):
            raise AssertionError(f"Locale {loc!r} events not a dict")
        for rank in _ALL_RANKS:
            if rank not in events:
                raise AssertionError(f"Missing locale event rank {rank!r} in {loc!r}")
    for table, rows in _witch_storyline().items():
        for rank in _ALL_RANKS:
            if rank not in rows:
                raise AssertionError(f"Missing witch clue rank {rank!r} in {table!r}")
    return True
