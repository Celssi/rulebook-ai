"""San Sibilia shortcuts: card draws and journal prompts."""

from __future__ import annotations

from typing import Literal, TypedDict

from src.games.sansibilia.curated import (
    day_one_prompts,
    detect_city_change,
    ending_prompts,
    format_character_draw,
    format_day_draw,
    score_for_turn,
)
from src.play_tools import draw_cards, format_dice_result, roll_dice

GAME_SANSIBILIA = "sansibilia"

ShortcutKind = Literal["multi_draw", "roll", "static", "rag_only"]

MULTI_DRAW_SHORTCUTS = frozenset({"draw_character", "draw_day"})


class SansibiliaShortcut(TypedDict):
    id: str
    label: str
    kind: ShortcutKind


SHORTCUTS: list[SansibiliaShortcut] = [
    {"id": "draw_character", "label": "Draw character (2 cards)", "kind": "multi_draw"},
    {"id": "draw_day", "label": "Draw day's cards", "kind": "multi_draw"},
    {"id": "day_one_prompts", "label": "Day 1 journal prompts", "kind": "static"},
    {"id": "ending_prompts", "label": "Ending journal prompts", "kind": "static"},
    {"id": "roll_days_between", "label": "Roll days between entries (d6)", "kind": "roll"},
    {"id": "city_change_help", "label": "City change rules", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def shortcuts_for_visit(*, visit_complete: bool = False) -> list[SansibiliaShortcut]:
    out = list(SHORTCUTS)
    if visit_complete:
        return [s for s in out if s["id"] in ("ending_prompts", "city_change_help")]
    return out


def match_sansibilia_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(
        p in lower
        for p in ("draw character", "character creation", "two cards for character", "draw two cards")
    ):
        return "draw_character"
    if any(
        p in lower
        for p in (
            "draw day",
            "day's cards",
            "days cards",
            "daily draw",
            "journal draw",
            "draw day's cards",
        )
    ):
        return "draw_day"
    if "day 1" in lower or "day one" in lower:
        return "day_one_prompts"
    if "ending prompt" in lower or "end of your stay" in lower or "final entry" in lower:
        return "ending_prompts"
    if "days between" in lower or "roll d6" in lower and "day" in lower:
        return "roll_days_between"
    if "city change" in lower:
        return "city_change_help"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_SANSIBILIA,
    char_id: str | None = None,
    card_source: str = "virtual",
    ending_mode: str = "four_changes",
    ace_value: int = 11,
    visit_day: int = 1,
    cards: list[str] | None = None,
) -> dict:
    """Return user_message + prompt for RAG, or static answer fields."""
    if shortcut_id == "draw_character":
        drawn = cards or _draw(game_id, char_id, card_source, 2)
        result = format_character_draw(drawn)
        user = (
            f"**Character draw:** {result['card1']} (trait) · {result['card2']} (role)\n\n"
            f"**{result['archetype']}**"
        )
        return {
            "user_message": user,
            "prompt": user,
            "draw_result": result,
            "cards": drawn,
            "static": True,
        }

    if shortcut_id == "draw_day":
        drawn = cards or _draw(game_id, char_id, card_source, 2)
        day = format_day_draw(drawn[0], drawn[1])
        user = (
            f"**Day {visit_day} draw:** {drawn[0]} (adjective) · {drawn[1]} (location/event)\n\n"
            f"**{day['adjective']}** + **{day['location_event']}**"
        )
        if day["city_change"]:
            ch = day["city_change"]
            user += f"\n\n**City change!** {ch['title']}\n{ch['prompt']}"
        turn_score = 0
        if ending_mode == "score_90":
            turn_score = score_for_turn(drawn, ace_value=ace_value)
            user += f"\n\nTurn score (+{turn_score} to tally; ace as {ace_value})"
        prompt = (
            f"San Sibilia journal day {visit_day}. Cards drawn: {drawn[0]} then {drawn[1]}. "
            f"Adjective (first card): {day['adjective']}. "
            f"Location/event (second card): {day['location_event']}. "
            f"Combined prompt: {day['prompt']}. "
        )
        if day["city_change"]:
            prompt += (
                f"City change triggered ({day['city_change']['kind']}): "
                f"{day['city_change']['title']} — {day['city_change']['prompt']} "
            )
        if ending_mode == "score_90":
            prompt += f"Alternative scoring: add {turn_score} to running tally. "
        prompt += "Briefly explain how to journal this entry per the rules."
        return {
            "user_message": user,
            "prompt": prompt,
            "draw_result": day,
            "cards": drawn,
            "turn_score": turn_score,
        }

    if shortcut_id == "day_one_prompts":
        qs = day_one_prompts()
        body = "\n".join(f"- {q}" for q in qs)
        msg = f"**Day 1 journal prompts**\n\n{body}"
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "ending_prompts":
        qs = ending_prompts()
        body = "\n".join(f"- {q}" for q in qs)
        msg = f"**The End of Your Stay — journal prompts**\n\n{body}"
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "roll_days_between":
        result = roll_dice("d6")
        msg = f"**Days between entries:** {format_dice_result(result)}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result}

    if shortcut_id == "city_change_help":
        prompt = (
            "Explain San Sibilia city changes: when two drawn cards share the same suit "
            "or the same value, the city changes and the player checks off one of four boxes. "
            "Describe each suit-pair prompt and the same-value prompt."
        )
        return {
            "user_message": "**City change rules**",
            "prompt": prompt,
        }

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}


def _draw(game_id: str, char_id: str | None, card_source: str, count: int) -> list[str]:
    if card_source == "physical":
        raise ValueError("Physical deck mode: report your cards in chat or switch to virtual deck.")
    result = draw_cards(count=count, game_id=game_id, char_id=char_id)
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    return list(result.get("cards") or [])
