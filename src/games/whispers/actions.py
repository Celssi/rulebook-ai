"""Whispers in the Walls shortcuts."""

from __future__ import annotations

from typing import Literal, TypedDict

from src.games.whispers.curated import (
    build_whispers_deck,
    format_card_draw,
    format_prompt_block,
    lookup_joker_prompt,
    lookup_oracle,
)
from src.play_tools import format_dice_result, roll_dice

GAME_WHISPERS = "whispers"

ShortcutKind = Literal["multi_draw", "roll", "static", "rag_only"]


class WhispersShortcut(TypedDict):
    id: str
    label: str
    kind: ShortcutKind


SHORTCUTS: list[WhispersShortcut] = [
    {"id": "build_deck", "label": "Build Whispers deck", "kind": "multi_draw"},
    {"id": "draw_whisper", "label": "Draw from Whispers deck", "kind": "multi_draw"},
    {"id": "oracle", "label": "Oracle (2d6)", "kind": "roll"},
    {"id": "deck_rules", "label": "Whispers deck rules", "kind": "rag_only"},
    {"id": "joker_ending", "label": "Joker's ending", "kind": "static"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def shortcuts_for_investigation(
    *,
    deck_built: bool = False,
    investigation_complete: bool = False,
    force_joker_ending: bool = False,
) -> list[WhispersShortcut]:
    if investigation_complete or force_joker_ending:
        return [s for s in SHORTCUTS if s["id"] in ("joker_ending", "oracle")]
    if not deck_built:
        return [s for s in SHORTCUTS if s["id"] in ("build_deck", "deck_rules", "oracle")]
    return [s for s in SHORTCUTS if s["id"] != "build_deck"]


def match_whispers_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(p in lower for p in ("build whispers", "build deck", "construct whispers", "new whispers deck")):
        return "build_deck"
    if any(
        p in lower
        for p in (
            "draw whisper",
            "draw from whispers",
            "whispers deck",
            "next card",
            "draw card from deck",
        )
    ):
        if "build" not in lower:
            return "draw_whisper"
    if "oracle" in lower or ("roll" in lower and "2d6" in lower):
        return "oracle"
    if "deck rules" in lower or "construct the whispers" in lower:
        return "deck_rules"
    if "joker ending" in lower or "joker's ending" in lower:
        return "joker_ending"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    difficulty: str = "normal",
    extra_secrets: int = 0,
    whispers_deck: list[str] | None = None,
    jokers_drawn: int = 0,
    card: str | None = None,
) -> dict:
    if shortcut_id == "build_deck":
        deck = whispers_deck or build_whispers_deck(difficulty=difficulty, extra_secrets=extra_secrets)
        if not deck:
            raise ValueError("Failed to build Whispers deck.")
        location_card = deck[0]
        remaining = deck[1:]
        draw = format_card_draw(location_card, is_location=True)
        user = (
            f"**Whispers deck built** ({len(deck)} cards)\n\n"
            f"**Location draw:** {location_card}\n\n{draw['prompt']}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "deck": remaining,
            "location_card": location_card,
            "draw_result": draw,
            "static": True,
        }

    if shortcut_id == "draw_whisper":
        if not whispers_deck:
            raise ValueError("Whispers deck is empty — build the deck first or start a new investigation.")
        drawn = card or whispers_deck[0]
        is_final = len(whispers_deck) == 1
        draw = format_card_draw(
            drawn,
            jokers_drawn_before=jokers_drawn,
            is_final_card=is_final,
        )
        label = "Final draw" if is_final else "Whisper draw"
        user = f"**{label}:** {drawn}\n\n{draw['prompt']}"
        if draw.get("trigger_joker_ending"):
            user += f"\n\n**All jokers revealed** — resolve the Joker's Ending:\n\n{draw['ending']}"
        return {
            "user_message": user,
            "prompt": user,
            "card": drawn,
            "draw_result": draw,
            "is_final": is_final,
        }

    if shortcut_id == "oracle":
        result = roll_dice("2d6")
        total = int(result.get("total") or 0)
        answer = lookup_oracle(total)
        msg = f"**Oracle (2d6):** {format_dice_result(result)}\n\n{answer}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result}

    if shortcut_id == "deck_rules":
        prompt = (
            "Explain how to construct the Whispers deck in Whispers in the Walls: "
            "Hollows deck (jokers + spades), Secrets deck (hearts, diamonds, clubs), "
            "draw 3 + 6 without looking, shuffle into 9 cards, draw first for location. "
            "Mention easy vs normal difficulty and optional extra secrets for longer play."
        )
        return {"user_message": "**Whispers deck rules**", "prompt": prompt}

    if shortcut_id == "joker_ending":
        body = lookup_joker_prompt("all_revealed")
        msg = format_prompt_block("Joker's Ending", body)
        return {"user_message": msg, "prompt": msg, "static": True}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
