"""Apothecaria game state transitions and economy."""

from __future__ import annotations

from typing import Any

from src.games.apothecaria.curated import (
    format_forage_draw,
    lookup_reagent,
    parse_playing_card,
    rank_numeric,
    reputation_tier,
    silver_base_rate,
)
from src.games.apothecaria.cottage import WitchCottage

STARTER_TOOLS = ("mortar", "cauldron", "alembic")
LOCALE_UNLOCK = {
    "blastfire_bog": "coracle",
    "cloud_isles": "broom",
    "dreamwater_depths": "bas_bata_cured",
    "the_strange": "portal_open",
}
BASE_LOCALES = frozenset({"glimmerwood", "meltwater_loch", "moonbreaker_mountain", "heros_hollow", "village"})


SEASONS = ("spring", "summer", "autumn", "winter")


def has_tool(cottage: WitchCottage, tool_id: str) -> bool:
    return tool_id in cottage.tools_owned


def has_unlock(cottage: WitchCottage, unlock_id: str) -> bool:
    return unlock_id in cottage.unlocks


def can_access_locale(cottage: WitchCottage, locale_id: str) -> bool:
    if locale_id in BASE_LOCALES or locale_id == "village":
        return True
    need = LOCALE_UNLOCK.get(locale_id)
    if not need:
        return True
    if need in ("coracle", "broom"):
        return has_tool(cottage, need)
    return has_unlock(cottage, need)


def foraging_points_for_locale(cottage: WitchCottage, locale_id: str | None = None) -> int:
    loc = locale_id or cottage.current_locale
    return int(cottage.foraging_tracks.get(loc, 0))


def set_foraging_points(cottage: WitchCottage, locale_id: str, points: int) -> None:
    cottage.foraging_tracks[locale_id] = max(0, int(points))


def familiar_forager_bonus(cottage: WitchCottage, reagent_type: str, fv: int) -> int:
    skill = (cottage.familiar_skill or "").lower()
    if "forager" in skill and reagent_type == "PLANT":
        return max(1, fv - 2)
    if "hunter" in skill and reagent_type == "ANIMAL":
        return max(1, fv - 3)
    if "magic eye" in skill and reagent_type == "MAGIC":
        return max(1, fv - 3)
    return fv


def point_gain_per_miss(cottage: WitchCottage) -> int:
    return 2 if has_tool(cottage, "sickle") else 1


def apply_timer(cottage: WitchCottage, delta: int) -> None:
    if cottage.ailment_timer is None:
        return
    cottage.ailment_timer = max(0, cottage.ailment_timer + delta)
    if cottage.ailment_timer == 0 and cottage.ailment_name:
        cottage.phase = "consequence"


def change_locale(cottage: WitchCottage, new_locale: str) -> dict[str, Any]:
    if not can_access_locale(cottage, new_locale):
        raise ValueError(f"Locale {new_locale} is not unlocked yet.")
    old = cottage.current_locale
    cottage.current_locale = new_locale
    if old != new_locale and cottage.phase == "ailment":
        apply_timer(cottage, -1)
        cottage.turn_count += 1
    return {"from": old, "to": new_locale, "timer": cottage.ailment_timer}


def event_seen_key(locale: str, rank: str) -> str:
    return f"{locale}:{rank}"


def mark_event_seen(cottage: WitchCottage, locale: str, rank: str) -> None:
    key = event_seen_key(locale, rank)
    if key not in cottage.seen_events:
        cottage.seen_events.append(key)


def is_event_seen(cottage: WitchCottage, locale: str, rank: str) -> bool:
    return event_seen_key(locale, rank) in cottage.seen_events


def resolve_hunt_step(
    cottage: WitchCottage,
    card: str,
    *,
    target_name: str | None = None,
    target_fv: int | None = None,
) -> dict[str, Any]:
    """One forage draw while hunting a reagent."""
    loc = cottage.current_locale
    fmt = format_forage_draw(card, loc)
    rank = fmt.get("rank", "")
    numeric = int(fmt.get("numeric_value", 0))
    event = str(fmt.get("event", ""))
    repeat = is_event_seen(cottage, loc, rank) if cottage.phase == "ailment" else False
    if cottage.phase == "ailment" and not repeat:
        mark_event_seen(cottage, loc, rank)

    found = False
    target = target_name or cottage.hunting_reagent
    fv = target_fv if target_fv is not None else cottage.hunting_fv

    if target and fv is not None:
        reg = lookup_reagent(target) if not target_fv else None
        if reg:
            fv = familiar_forager_bonus(cottage, str(reg.get("type", "")), int(fv))
        if numeric >= fv:
            found = True
            cottage.inventory.append({"name": target, "fv": fv})
            cottage.hunting_reagent = ""
            cottage.hunting_fv = None
        else:
            pts = foraging_points_for_locale(cottage, loc) + point_gain_per_miss(cottage)
            set_foraging_points(cottage, loc, pts)
            if pts >= fv:
                found = True
                cottage.inventory.append({"name": target, "fv": fv})
                cottage.hunting_reagent = ""
                cottage.hunting_fv = None
                set_foraging_points(cottage, loc, 0)

    if cottage.phase == "ailment" and not repeat:
        apply_timer(cottage, -1)
        cottage.turn_count += 1

    return {
        **fmt,
        "found": found,
        "found_reagent": target if found else "",
        "foraging_points": foraging_points_for_locale(cottage, loc),
        "target": target,
        "target_fv": fv,
        "event_repeat": repeat,
    }


def compute_payment(cottage: WitchCottage, poison: int, sweet: int) -> dict[str, Any]:
    base = silver_base_rate(cottage.reputation)
    net_poison = max(0, poison - sweet)
    net_sweet = max(0, sweet - poison)
    silver = base - net_poison * 4 + net_sweet * 4
    if has_upgrade(cottage, "treatment_room"):
        silver += 10
    rejected = net_poison >= 5
    if rejected:
        silver = 0
    return {
        "base": base,
        "silver": max(0, silver),
        "rejected": rejected,
        "net_poison": net_poison,
        "net_sweet": net_sweet,
    }


def has_upgrade(cottage: WitchCottage, upgrade_id: str) -> bool:
    return upgrade_id in cottage.upgrades_owned


def complete_potion(cottage: WitchCottage, poison: int, sweet: int) -> dict[str, Any]:
    pay = compute_payment(cottage, poison, sweet)
    rep_delta = 0
    if pay["rejected"]:
        rep_delta = -1
    elif cottage.ailment_name:
        rep_delta = 1
    cottage.silver += pay["silver"]
    cottage.reputation = max(0, cottage.reputation + rep_delta)
    cottage.potion_poison = 0
    cottage.potion_sweet = 0
    cottage.inventory = []
    result = {
        "silver_gained": pay["silver"],
        "reputation_delta": rep_delta,
        "rejected": pay["rejected"],
        "cleared_ailment": cottage.ailment_name,
    }
    cottage.patient_name = ""
    cottage.patient_job = ""
    cottage.patient_type = ""
    cottage.ailment_name = ""
    cottage.ailment_tags = []
    cottage.ailment_timer = None
    cottage.hunting_reagent = ""
    cottage.hunting_fv = None
    cottage.foraging_tracks = {}
    cottage.seen_events = []
    cottage.turn_count = 0
    cottage.phase = "downtime"
    cottage.downtime_timer = 6
    return result


def advance_week(cottage: WitchCottage, *, downtime: bool = False) -> dict[str, Any]:
    festival = False
    cottage.week += 1
    if cottage.week > 13:
        cottage.week = 1
        idx = SEASONS.index(cottage.season) if cottage.season in SEASONS else 0
        cottage.season = SEASONS[(idx + 1) % 4]
        festival = True
        cottage.phase = "festival"
        cottage.seen_events = []
    elif downtime:
        cottage.phase = "ailment" if cottage.ailment_name else "idle"
    return {"week": cottage.week, "season": cottage.season, "festival": festival}


def start_ailment(
    cottage: WitchCottage,
    *,
    ailment_name: str,
    tags: list[str],
    timer: int | None,
    patient_type: str = "",
) -> None:
    cottage.ailment_name = ailment_name
    cottage.ailment_tags = list(tags)
    cottage.ailment_timer = timer
    cottage.patient_type = patient_type
    cottage.phase = "ailment"
    cottage.turn_count = 0
    cottage.foraging_tracks = {}
    cottage.seen_events = []
    cottage.hunting_reagent = ""
    cottage.hunting_fv = None
    cottage.current_locale = "glimmerwood"


def set_hunt_target(cottage: WitchCottage, reagent_name: str) -> dict[str, Any]:
    reg = lookup_reagent(reagent_name)
    if not reg:
        raise ValueError(f"Unknown reagent: {reagent_name}")
    locales = reg.get("locales") or {}
    loc = cottage.current_locale
    fv = locales.get(loc)
    if fv is None:
        if locales:
            loc, fv = min(locales.items(), key=lambda x: x[1])
            cottage.current_locale = loc
        else:
            fv = 5
    fv = familiar_forager_bonus(cottage, str(reg.get("type", "")), int(fv))
    cottage.hunting_reagent = reagent_name
    cottage.hunting_fv = fv
    set_foraging_points(cottage, cottage.current_locale, 0)
    return {"reagent": reagent_name, "locale": cottage.current_locale, "foraging_value": fv}


def potion_totals(cottage: WitchCottage) -> tuple[int, int]:
    poison = int(cottage.potion_poison or 0)
    sweet = int(cottage.potion_sweet or 0)
    for item in cottage.inventory:
        reg = lookup_reagent(str(item.get("name", "")))
        if reg:
            poison += int(reg.get("poison") or 0)
            sweet += int(reg.get("sweet") or 0)
    return poison, sweet


def advance_downtime(cottage: WitchCottage) -> dict[str, Any]:
    if cottage.phase != "downtime":
        raise ValueError("Not in downtime.")
    cottage.downtime_timer = max(0, cottage.downtime_timer - 1)
    done = cottage.downtime_timer == 0
    if done:
        cottage.phase = "idle"
    return {"remaining": cottage.downtime_timer, "done": done}


def buy_tool(cottage: WitchCottage, tool_id: str) -> dict[str, Any]:
    from src.games.apothecaria.curated import lookup_purchasable_tool

    tool = lookup_purchasable_tool(tool_id)
    if not tool:
        raise ValueError(f"Unknown tool: {tool_id}")
    cost = tool.get("cost")
    if cost is None:
        raise ValueError(f"{tool.get('name', tool_id)} is not sold in the shop.")
    cost = int(cost)
    if tool_id in cottage.tools_owned:
        raise ValueError(f"You already own {tool.get('name', tool_id)}.")
    if cottage.silver < cost:
        raise ValueError(f"Need {cost} Silver (have {cottage.silver}).")
    cottage.silver -= cost
    cottage.tools_owned.append(tool_id)
    return {"tool_id": tool_id, "name": tool.get("name", tool_id), "cost": cost, "silver": cottage.silver}


def buy_upgrade(cottage: WitchCottage, upgrade_id: str) -> dict[str, Any]:
    from src.games.apothecaria.curated import lookup_upgrade

    upgrade = lookup_upgrade(upgrade_id)
    if not upgrade:
        raise ValueError(f"Unknown upgrade: {upgrade_id}")
    rep_min = upgrade.get("rep_min")
    if rep_min is not None and cottage.reputation < int(rep_min):
        raise ValueError(f"Need reputation {rep_min}+ (have {cottage.reputation}).")
    cost = int(upgrade.get("cost") or 0)
    if upgrade_id in cottage.upgrades_owned:
        raise ValueError(f"You already own {upgrade.get('name', upgrade_id)}.")
    if cottage.silver < cost:
        raise ValueError(f"Need {cost} Silver (have {cottage.silver}).")
    cottage.silver -= cost
    cottage.upgrades_owned.append(upgrade_id)
    return {
        "upgrade_id": upgrade_id,
        "name": upgrade.get("name", upgrade_id),
        "cost": cost,
        "silver": cottage.silver,
    }
