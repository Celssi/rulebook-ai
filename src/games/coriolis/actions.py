"""Coriolis: The Great Dark shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.coriolis.curated import roll_despair_resist, roll_encounter, roll_mental_trauma
from src.games.gm_solo.dice import roll_great_dark

GAME_ID = "coriolis"

ShortcutKind = Literal["static", "rag_only", "roll", "roll_rag"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "attribute_roll", "label": "Attribute roll", "kind": "roll_rag"},
    {"id": "push_roll", "label": "Pushed roll", "kind": "roll_rag"},
    {"id": "despair_check", "label": "Despair check", "kind": "roll"},
    {"id": "encounter", "label": "Random encounter", "kind": "roll_rag"},
    {"id": "rules_help", "label": "Coriolis rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_coriolis_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if "attribute roll" in lower or "skill roll" in lower or "talent roll" in lower:
        return "attribute_roll"
    if "push roll" in lower or "pushed roll" in lower or "push dice" in lower:
        return "push_roll"
    if "despair check" in lower or "despair roll" in lower or "despair resist" in lower:
        return "despair_check"
    if "encounter" in lower or "random encounter" in lower:
        return "encounter"
    if "coriolis rules" in lower or "how to play coriolis" in lower:
        return "rules_help"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_ID,
    attribute: str = "perception",
    talent: str = "",
    base_pool: int = 3,
    gear_pool: int = 0,
    hope: int = 0,
    max_hope: int = 8,
    potential_despair: int = 1,
    crew_name: str = "",
    bird_name: str = "",
    shuttle_name: str = "",
) -> dict:
    _ = game_id

    if shortcut_id == "rules_help":
        prompt = (
            "Explain Coriolis: The Great Dark solo play basics — Lost Horizon, Explorers Guild, "
            "attribute + talent dice pools, base and gear dice, pushing rolls and Hope loss, "
            "Health Hope Heart, despair and Blight, crew and Bird. Cite the core rulebook."
        )
        return {"user_message": "**Coriolis rules**", "prompt": prompt, "rag_only": True}

    talent_label = f" + {talent}" if talent else ""

    if shortcut_id == "attribute_roll":
        dice = roll_great_dark(base_pool, gear_pool, pushed=False)
        user = f"**Attribute roll** ({attribute}{talent_label}, base {base_pool}"
        if gear_pool:
            user += f", gear {gear_pool}"
        user += f")\n\n{dice['summary']}"
        rag = (
            f"Coriolis: The Great Dark roll for {attribute}{talent_label}. "
            f"Crew {crew_name or 'unnamed'}, Bird {bird_name or 'unnamed'}. "
            f"{dice['summary']}. Explain outcome using Great Dark rules."
        )
        return {
            "user_message": user,
            "prompt": rag,
            "task": "attribute_roll",
            "dice": dice,
            "roll_summary": dice["summary"],
            "attribute": attribute,
            "talent": talent,
        }

    if shortcut_id == "push_roll":
        dice = roll_great_dark(base_pool, gear_pool, pushed=True)
        hope_loss = int(dice.get("base_ones", 0) or 0)
        gear_loss = int(dice.get("gear_ones", 0) or 0)
        new_hope = max(0, int(hope) - hope_loss)
        new_gear = max(0, int(gear_pool) - gear_loss)
        user = f"**Pushed roll** ({attribute}{talent_label})\n\n{dice['summary']}"
        rag = (
            f"Coriolis pushed roll for {attribute}{talent_label}. {dice['summary']}. "
            f"Hope loss from base 1s: {hope_loss}. Gear penalty dice: {gear_loss}. Explain consequences."
        )
        result: dict = {
            "user_message": user,
            "prompt": rag,
            "task": "push_roll",
            "dice": dice,
            "roll_summary": dice["summary"],
            "attribute": attribute,
            "talent": talent,
            "hope": new_hope,
            "hope_delta": -hope_loss,
            "gear_bonus": new_gear,
            "gear_delta": -gear_loss,
        }
        if new_hope <= 0 and max_hope > 0:
            trauma = roll_mental_trauma()
            result["mental_trauma"] = trauma
            result["roll_summary"] = dice["summary"] + "\n\n" + trauma["summary"]
            result["user_message"] = user + "\n\n" + trauma["summary"]
        return result

    if shortcut_id == "despair_check":
        despair = roll_despair_resist(base_pool, potential_despair=potential_despair, pushed=False)
        new_hope = max(0, int(hope) - int(despair.get("despair_taken", 0) or 0))
        user = f"**Despair check** (potential {potential_despair})\n\n{despair['summary']}"
        result = {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "despair_check",
            "roll_summary": despair["summary"],
            "despair": despair,
            "hope": new_hope,
            "hope_delta": -(int(despair.get("despair_taken", 0) or 0)),
        }
        if new_hope <= 0 and max_hope > 0:
            trauma = roll_mental_trauma()
            result["mental_trauma"] = trauma
            result["roll_summary"] = despair["summary"] + "\n\n" + trauma["summary"]
            result["user_message"] = user + "\n\n" + trauma["summary"]
        return result

    if shortcut_id == "encounter":
        enc = roll_encounter()
        user = f"**Encounter** ({enc['category']})\n\n{enc['text']}"
        rag = (
            f"Coriolis: The Great Dark encounter for crew {crew_name or 'unnamed'}, "
            f"Bird {bird_name or 'unnamed'}, shuttle {shuttle_name or 'unnamed'}. "
            f"{enc['text']}. Frame a delve or voyage scene and possible attribute tests."
        )
        return {
            "user_message": user,
            "prompt": rag,
            "task": "encounter",
            "encounter": enc,
        }

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
