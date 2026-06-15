"""The One Ring Strider Mode curated tables."""

from __future__ import annotations

import random
from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR

_TELLING_PATH = CURATED_DIR / "tor_telling.yaml"
_FORTUNE_PATH = CURATED_DIR / "tor_fortune.yaml"
_LORE_PATH = CURATED_DIR / "tor_lore.yaml"
_PATRON_PATH = CURATED_DIR / "tor_patron_quests.yaml"
_JOURNEY_PATH = CURATED_DIR / "tor_journey_events.yaml"
_JOURNEY_DETAIL_PATH = CURATED_DIR / "tor_journey_event_details.yaml"
_MILESTONES_PATH = CURATED_DIR / "tor_experience_milestones.yaml"
_HUNT_PATH = CURATED_DIR / "tor_hunt_tables.yaml"
_REVELATION_PATH = CURATED_DIR / "tor_revelation_episodes.yaml"

_FEAT_ICON = {11: "gandalf", 12: "sauron"}

_JOURNEY_EVENT_TYPES = {
    "gandalf": "terrible_misfortune",
    "1": "despair",
    "2": "ill_choices",
    "3": "ill_choices",
    "4": "mishap",
    "5": "mishap",
    "6": "mishap",
    "7": "mishap",
    "8": "short_cut",
    "9": "short_cut",
    "10": "chance_meeting",
    "sauron": "joyful_sight",
}


def _load_yaml(path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=1)
def _telling() -> dict[str, Any]:
    return _load_yaml(_TELLING_PATH)


@lru_cache(maxsize=1)
def _fortune_tables() -> dict[str, Any]:
    return _load_yaml(_FORTUNE_PATH)


@lru_cache(maxsize=1)
def _lore_sections() -> dict[str, Any]:
    data = _load_yaml(_LORE_PATH)
    return data.get("sections") or {}


@lru_cache(maxsize=1)
def _patrons() -> dict[str, Any]:
    data = _load_yaml(_PATRON_PATH)
    return data.get("patrons") or {}


@lru_cache(maxsize=1)
def _journey_events() -> dict[str, Any]:
    data = _load_yaml(_JOURNEY_PATH)
    return data.get("events") or {}


@lru_cache(maxsize=1)
def _journey_event_details() -> dict[str, Any]:
    return _load_yaml(_JOURNEY_DETAIL_PATH)


@lru_cache(maxsize=1)
def _milestones() -> dict[str, Any]:
    data = _load_yaml(_MILESTONES_PATH)
    return data.get("milestones") or {}


@lru_cache(maxsize=1)
def _hunt_tables() -> dict[str, Any]:
    return _load_yaml(_HUNT_PATH)


@lru_cache(maxsize=1)
def _revelation_episodes() -> dict[str, Any]:
    data = _load_yaml(_REVELATION_PATH)
    return data.get("episodes") or {}


def feat_key(feat_roll: int) -> str:
    icon = _FEAT_ICON.get(int(feat_roll))
    if icon:
        return icon
    return str(max(1, min(10, int(feat_roll))))


def roll_feat_die() -> int:
    return random.randint(1, 12)


def roll_success_die() -> int:
    return random.randint(1, 6)


def lookup_telling_chance(chance: str) -> dict[str, Any]:
    chances = _telling().get("chances") or {}
    entry = chances.get(chance) if isinstance(chances, dict) else None
    if not isinstance(entry, dict):
        entry = chances.get("middling", {}) if isinstance(chances, dict) else {}
    special = _telling().get("special") or {}
    return {
        "chance": chance,
        "min_roll": int(entry.get("min_roll", 6) or 6),
        "gandalf": str(special.get("gandalf_rune", "yes_with_twist")),
        "sauron": str(special.get("sauron_icon", "no_with_twist")),
    }


def resolve_telling(feat_roll: int, chance: str = "middling") -> dict[str, Any]:
    cfg = lookup_telling_chance(chance)
    icon = _FEAT_ICON.get(int(feat_roll), "")
    if icon == "gandalf":
        return {
            "feat": feat_roll,
            "feat_icon": icon,
            "chance": chance,
            "answer": "yes",
            "twist": "extreme result or twist",
            "summary": f"Telling Table ({chance}): Feat **{feat_roll}** — Gandalf rune — **Yes**, with an extreme twist",
        }
    if icon == "sauron":
        return {
            "feat": feat_roll,
            "feat_icon": icon,
            "chance": chance,
            "answer": "no",
            "twist": "extreme result or twist",
            "summary": f"Telling Table ({chance}): Feat **{feat_roll}** — Eye of Sauron — **No**, with an extreme twist",
        }
    min_roll = int(cfg["min_roll"])
    yes = int(feat_roll) >= min_roll
    answer = "yes" if yes else "no"
    return {
        "feat": feat_roll,
        "feat_icon": "",
        "chance": chance,
        "answer": answer,
        "min_roll": min_roll,
        "summary": (
            f"Telling Table ({chance}): Feat **{feat_roll}** — need {min_roll}+ — **{answer.title()}**"
        ),
    }


def roll_telling(chance: str = "middling") -> dict[str, Any]:
    feat = roll_feat_die()
    result = resolve_telling(feat, chance)
    result["rolled"] = True
    return result


def lookup_fortune(feat_roll: int, *, ill: bool = False) -> dict[str, Any]:
    tables = _fortune_tables()
    table = tables.get("ill_fortune" if ill else "fortune") or {}
    key = feat_key(feat_roll)
    entry = table.get(key) if isinstance(table, dict) else None
    if not isinstance(entry, dict):
        entry = table.get(str(feat_roll), {}) if isinstance(table, dict) else {}
    text = str(entry.get("text", "") or "")
    delta = entry.get("eye_awareness_delta")
    return {
        "feat": feat_roll,
        "feat_key": key,
        "text": text,
        "eye_awareness_delta": int(delta) if delta is not None else 0,
    }


def roll_fortune(*, ill: bool = False) -> dict[str, Any]:
    feat = roll_feat_die()
    row = lookup_fortune(feat, ill=ill)
    label = "Ill-Fortune" if ill else "Fortune"
    icon_note = ""
    if row["feat_key"] == "gandalf":
        icon_note = " (Gandalf rune)"
    elif row["feat_key"] == "sauron":
        icon_note = " (Eye of Sauron)"
    summary = f"{label} Table: Feat **{feat}**{icon_note} — {row['text']}"
    return {**row, "ill": ill, "summary": summary}


def lookup_lore(feat_roll: int, success_roll: int) -> dict[str, str]:
    sections = _lore_sections()
    section_key = feat_key(feat_roll)
    section = sections.get(section_key) if isinstance(sections, dict) else None
    if not isinstance(section, dict):
        return {"action": "", "aspect": "", "focus": ""}
    row = section.get(str(success_roll)) or section.get(str(int(success_roll)))
    if not isinstance(row, dict):
        return {"action": "", "aspect": "", "focus": ""}
    return {
        "action": str(row.get("action", "") or ""),
        "aspect": str(row.get("aspect", "") or ""),
        "focus": str(row.get("focus", "") or ""),
    }


def roll_lore_draw() -> dict[str, Any]:
    feat = roll_feat_die()
    success = roll_success_die()
    row = lookup_lore(feat, success)
    phrase = " · ".join(p for p in (row["action"], row["aspect"], row["focus"]) if p)
    icon = _FEAT_ICON.get(feat, "")
    icon_note = f" ({icon})" if icon else ""
    summary = f"Lore Table: Feat **{feat}**{icon_note}, Success **{success}** — **{phrase}**"
    return {
        "feat": feat,
        "success": success,
        "feat_icon": icon,
        **row,
        "phrase": phrase,
        "summary": summary,
    }


def patron_ids() -> list[str]:
    patrons = _patrons()
    return sorted(patrons.keys()) if isinstance(patrons, dict) else []


def lookup_patron(patron_id: str) -> dict[str, Any]:
    patrons = _patrons()
    entry = patrons.get(patron_id) if isinstance(patrons, dict) else None
    if not isinstance(entry, dict):
        return {"id": patron_id, "label": patron_id, "quests": {}}
    quests = entry.get("quests") or {}
    return {
        "id": patron_id,
        "label": str(entry.get("label", patron_id) or patron_id),
        "quests": dict(quests) if isinstance(quests, dict) else {},
    }


def roll_patron_quest(patron_id: str) -> dict[str, Any]:
    patron = lookup_patron(patron_id)
    quests = patron.get("quests") or {}
    roll = roll_success_die()
    text = str(quests.get(str(roll), "") or "")
    summary = (
        f"Patron quest ({patron['label']}): d6 = **{roll}**\n\n{text}"
        if text
        else f"Patron quest ({patron['label']}): d6 = **{roll}** — (no entry)"
    )
    return {
        "patron_id": patron_id,
        "patron_label": patron["label"],
        "roll": roll,
        "quest": text,
        "summary": summary,
    }


def journey_event_type(feat_roll: int) -> str:
    key = feat_key(feat_roll)
    return _JOURNEY_EVENT_TYPES.get(key, "mishap")


def lookup_journey_event(feat_roll: int) -> dict[str, Any]:
    events = _journey_events()
    key = feat_key(feat_roll)
    entry = events.get(key) if isinstance(events, dict) else None
    if not isinstance(entry, dict):
        entry = events.get(str(feat_roll), {}) if isinstance(events, dict) else {}
    return {
        "feat": feat_roll,
        "feat_key": key,
        "event_type": journey_event_type(feat_roll),
        "event": str(entry.get("event", "") or ""),
        "fail": str(entry.get("fail", "") or ""),
        "success": str(entry.get("success", "") or ""),
        "fatigue": int(entry.get("fatigue", 0) or 0),
    }


def lookup_journey_event_detail(event_type: str, success_roll: int) -> dict[str, str]:
    details = _journey_event_details()
    section = details.get(event_type) if isinstance(details, dict) else None
    if not isinstance(section, dict):
        return {"event": "", "outcome": ""}
    row = section.get(str(success_roll)) or section.get(str(int(success_roll)))
    if not isinstance(row, dict):
        return {"event": "", "outcome": ""}
    return {
        "event": str(row.get("event", "") or ""),
        "outcome": str(row.get("outcome", "") or ""),
    }


def lookup_revelation_episode(feat_roll: int) -> dict[str, Any]:
    episodes = _revelation_episodes()
    key = feat_key(feat_roll)
    raw = episodes.get(key) if isinstance(episodes, dict) else None
    if isinstance(raw, dict):
        text = str(raw.get("text", "") or "")
    else:
        text = str(raw or "")
    return {"feat": feat_roll, "feat_key": key, "episode": text}


def roll_revelation_episode() -> dict[str, Any]:
    feat = roll_feat_die()
    row = lookup_revelation_episode(feat)
    icon = _FEAT_ICON.get(feat, "")
    icon_note = f" ({icon})" if icon else ""
    summary = f"Revelation Episode: Feat **{feat}**{icon_note} — **{row['episode']}**"
    return {**row, "feat_icon": icon, "summary": summary}


def lookup_hunt_threshold(region_id: str = "wild") -> dict[str, Any]:
    tables = _hunt_tables()
    regions = tables.get("regions") or {}
    region = regions.get(region_id) if isinstance(regions, dict) else None
    if not isinstance(region, dict):
        region = regions.get("wild", {}) if isinstance(regions, dict) else {}
    modifiers = tables.get("modifiers") or {}
    mod_list = []
    if isinstance(modifiers, dict):
        for mid, entry in modifiers.items():
            if isinstance(entry, dict):
                mod_list.append({
                    "id": mid,
                    "modifier": int(entry.get("modifier", 0) or 0),
                    "text": str(entry.get("text", "") or ""),
                })
    return {
        "region_id": region_id,
        "region_label": str(region.get("label", region_id) or region_id),
        "threshold": int(region.get("threshold", 16) or 16),
        "modifiers": mod_list,
    }


def format_hunt_threshold(region_id: str = "wild") -> str:
    row = lookup_hunt_threshold(region_id)
    lines = [
        f"**Hunt threshold** ({row['region_label']}): **{row['threshold']}**",
        "",
        "Modifiers (apply to threshold):",
    ]
    for m in row["modifiers"]:
        sign = "+" if m["modifier"] >= 0 else ""
        lines.append(f"- {sign}{m['modifier']}: {m['text']}")
    return "\n".join(lines)


def format_milestones_table() -> str:
    milestones = _milestones()
    if not isinstance(milestones, dict):
        return ""
    lines = ["**Experience Milestones** (Strider Mode)", ""]
    for entry in milestones.values():
        if not isinstance(entry, dict):
            continue
        label = str(entry.get("label", "") or "")
        ap = int(entry.get("adventure_points", 0) or 0)
        sp = int(entry.get("skill_points", 0) or 0)
        parts = []
        if ap:
            parts.append(f"{ap} Adventure Point{'s' if ap != 1 else ''}")
        if sp:
            parts.append(f"{sp} Skill Point{'s' if sp != 1 else ''}")
        reward = " and ".join(parts) if parts else "(see rules)"
        lines.append(f"- **{label}** — {reward}")
    return "\n".join(lines)


def roll_journey_event() -> dict[str, Any]:
    feat = roll_feat_die()
    success = roll_success_die()
    row = lookup_journey_event(feat)
    detail = lookup_journey_event_detail(row["event_type"], success)
    icon = _FEAT_ICON.get(feat, "")
    icon_note = f" ({icon})" if icon else ""
    lines = [
        f"Solo Journey Event: Feat **{feat}**{icon_note}, Success **{success}** — **{row['event']}**",
    ]
    if detail["event"]:
        lines.append(f"- Detail: **{detail['event']}**")
    if detail["outcome"]:
        lines.append(f"- Test: {detail['outcome']}")
    if row["fail"]:
        lines.append(f"- On failure: {row['fail']}")
    if row["success"]:
        lines.append(f"- On success: {row['success']}")
    if row["fatigue"]:
        lines.append(f"- Fatigue points gained: {row['fatigue']}")
    summary = "\n".join(lines)
    return {
        **row,
        "success_roll": success,
        "detail_event": detail["event"],
        "detail_outcome": detail["outcome"],
        "feat_icon": icon,
        "summary": summary,
    }


def all_tables_valid() -> bool:
    chances = _telling().get("chances") or {}
    for key in ("certain", "likely", "middling", "doubtful", "unthinkable"):
        if key not in chances:
            return False
    fortune = _fortune_tables().get("fortune") or {}
    ill = _fortune_tables().get("ill_fortune") or {}
    for table in (fortune, ill):
        for k in ("1", "10", "gandalf", "sauron"):
            if k not in table:
                return False
    sections = _lore_sections()
    for feat in [str(i) for i in range(1, 11)] + ["gandalf", "sauron"]:
        sec = sections.get(feat)
        if not isinstance(sec, dict):
            return False
        for succ in ("1", "6"):
            if succ not in sec:
                return False
    for pid in ("bilbo", "gandalf", "gilraen", "balin", "cirdan", "tom_goldberry"):
        patron = lookup_patron(pid)
        if len(patron.get("quests") or {}) != 6:
            return False
    events = _journey_events()
    for k in ("gandalf", "1", "10", "sauron"):
        if k not in events:
            return False
    details = _journey_event_details()
    for etype in (
        "terrible_misfortune",
        "despair",
        "ill_choices",
        "mishap",
        "short_cut",
        "chance_meeting",
        "joyful_sight",
    ):
        sec = details.get(etype)
        if not isinstance(sec, dict):
            return False
        for succ in ("1", "6"):
            if succ not in sec:
                return False
    milestones = _milestones()
    if len(milestones) != 10:
        return False
    hunt = _hunt_tables()
    regions = hunt.get("regions") or {}
    for rid in ("border", "wild", "dark"):
        if rid not in regions:
            return False
    if len(hunt.get("modifiers") or {}) != 4:
        return False
    revelation = _revelation_episodes()
    for k in ("gandalf", "1", "10", "sauron"):
        if k not in revelation:
            return False
    return True
