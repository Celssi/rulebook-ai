"""The One Ring Strider Mode shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.gm_solo.dice import roll_tor_skill
from src.games.tor.curated import (
    format_hunt_threshold,
    format_milestones_table,
    roll_fortune,
    roll_journey_event,
    roll_lore_draw,
    roll_patron_quest,
    roll_revelation_episode,
    roll_telling,
)

GAME_ID = "tor"

ShortcutKind = Literal["roll", "roll_rag", "rag_only", "static"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "telling_oracle", "label": "Telling Table", "kind": "roll"},
    {"id": "lore_draw", "label": "Lore Table draw", "kind": "roll"},
    {"id": "patron_quest", "label": "Patron quest", "kind": "roll"},
    {"id": "fortune", "label": "Fortune", "kind": "roll"},
    {"id": "ill_fortune", "label": "Ill-Fortune", "kind": "roll"},
    {"id": "tor_skill", "label": "Skill roll", "kind": "roll_rag"},
    {"id": "journey_event", "label": "Journey event", "kind": "roll_rag"},
    {"id": "milestones_help", "label": "Experience milestones", "kind": "static"},
    {"id": "hunt_threshold", "label": "Hunt threshold", "kind": "static"},
    {"id": "revelation_episode", "label": "Revelation episode", "kind": "roll"},
    {"id": "rules_help", "label": "One Ring rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_tor_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if "telling table" in lower or "telling oracle" in lower:
        return "telling_oracle"
    if "lore table" in lower or "lore draw" in lower:
        return "lore_draw"
    if "patron quest" in lower or "roll patron" in lower:
        return "patron_quest"
    if "ill-fortune" in lower or "ill fortune" in lower:
        return "ill_fortune"
    if "fortune table" in lower or lower == "fortune":
        return "fortune"
    if "journey event" in lower or "solo journey" in lower:
        return "journey_event"
    if "experience milestone" in lower or "milestones help" in lower:
        return "milestones_help"
    if "hunt threshold" in lower or "hunt modifier" in lower:
        return "hunt_threshold"
    if "revelation episode" in lower or "revelation event" in lower:
        return "revelation_episode"
    if "skill roll" in lower or "tor skill" in lower or "one ring skill" in lower:
        return "tor_skill"
    if "one ring rules" in lower or "strider mode" in lower or "how to play tor" in lower:
        return "rules_help"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_ID,
    name: str = "",
    culture: str = "",
    calling: str = "",
    patron: str = "",
    hope: int = 0,
    dread: int = 0,
    weary: bool = False,
    strider: bool = True,
    eye_awareness: int = 0,
    safe_haven: str = "",
    journey_day: int = 0,
    hunt_region: str = "wild",
    telling_chance: str = "middling",
    success_dice: int = 1,
    **_kwargs,
) -> dict:
    _ = game_id
    who = name.strip() or "the hero"
    context = f"{who}"
    if culture or calling:
        context = f"{who} ({culture} {calling})".strip()

    if shortcut_id == "telling_oracle":
        result = roll_telling(telling_chance)
        user = f"**Telling Table** ({telling_chance})\n\n{result['summary']}"
        return {"user_message": user, "prompt": user, "static": True, "telling": result}

    if shortcut_id == "lore_draw":
        result = roll_lore_draw()
        user = f"**Lore Table**\n\n{result['summary']}"
        prompt = (
            f"One Ring Strider Mode Lore Table draw for {context}: {result['phrase']}. "
            f"Suggest how to interpret Action, Aspect, and Focus in the current scene."
        )
        return {"user_message": user, "prompt": prompt, "lore": result}

    if shortcut_id == "patron_quest":
        patron_id = patron.strip() or "gandalf"
        result = roll_patron_quest(patron_id)
        user = f"**Patron quest**\n\n{result['summary']}"
        prompt = (
            f"One Ring patron mission for {context} from {result['patron_label']}: "
            f"{result['quest']}. Frame this as an adventure hook using Strider Mode guidance."
        )
        return {"user_message": user, "prompt": prompt, "patron_quest": result}

    if shortcut_id == "fortune":
        result = roll_fortune(ill=False)
        user = f"**Fortune**\n\n{result['summary']}"
        delta = result.get("eye_awareness_delta", 0)
        patch = {}
        if delta:
            patch["eye_awareness_delta"] = delta
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "fortune": result,
            "entity_patch": patch,
        }

    if shortcut_id == "ill_fortune":
        result = roll_fortune(ill=True)
        user = f"**Ill-Fortune**\n\n{result['summary']}"
        delta = result.get("eye_awareness_delta", 0)
        patch = {}
        if delta:
            patch["eye_awareness_delta"] = delta
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "fortune": result,
            "entity_patch": patch,
        }

    if shortcut_id == "tor_skill":
        dice = roll_tor_skill(success_dice)
        weary_note = " (Weary — remember to downgrade Feat die)" if weary else ""
        strider_note = " (Strider — Inspired on journey skill rolls)" if strider else ""
        user = f"**Skill roll**{weary_note}{strider_note}\n\n{dice['summary']}"
        prompt = (
            f"One Ring skill roll for {context}. Hope {hope}, Dread {dread}, "
            f"Eye Awareness {eye_awareness}. {dice['summary']}. "
            f"Explain target number, success icons, and Strider Mode consequences using the rules."
        )
        return {"user_message": user, "prompt": prompt, "dice": dice, "task": "tor_skill"}

    if shortcut_id == "journey_event":
        result = roll_journey_event()
        haven = safe_haven or "(unset)"
        user = (
            f"**Journey event** (day {journey_day}, haven: {haven})\n\n"
            f"{result['summary']}"
        )
        prompt = (
            f"One Ring solo journey event for {context} on journey day {journey_day}. "
            f"{result['summary']}. Resolve using the indicated skill test and Strider Mode journey rules."
        )
        return {"user_message": user, "prompt": prompt, "journey": result, "task": "journey_event"}

    if shortcut_id == "milestones_help":
        text = format_milestones_table()
        return {"user_message": text, "prompt": text, "static": True}

    if shortcut_id == "hunt_threshold":
        region = (hunt_region or "wild").strip().lower()
        text = format_hunt_threshold(region)
        return {"user_message": text, "prompt": text, "static": True}

    if shortcut_id == "revelation_episode":
        result = roll_revelation_episode()
        user = f"**Revelation episode**\n\n{result['summary']}"
        prompt = (
            f"One Ring Revelation Episode for {context} (safe haven: {safe_haven or 'unset'}): "
            f"{result['episode']}. Frame this as a Fellowship Phase complication using Strider Mode."
        )
        return {"user_message": user, "prompt": prompt, "revelation": result}

    if shortcut_id == "rules_help":
        prompt = (
            "Explain how to play The One Ring in Strider Mode solo: Telling Table, Lore Table, "
            "Fortune and Ill-Fortune, patron quests, Eye Awareness, journeys, councils, and combat "
            "for a lone Player-hero. Cite Strider Mode and core rules."
        )
        return {"user_message": "**One Ring rules**", "prompt": prompt, "rag_only": True}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
