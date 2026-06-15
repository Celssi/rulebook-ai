"""Lighthouse shortcuts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from src.games.lighthouse.curated import (
    beachcombing_card_count,
    ending_text,
    flip_coin,
    format_beachcombing_find,
    format_event,
    format_light_lamp,
    format_maintenance,
    format_observation,
    lookup_weather,
    order_of_play_text,
    task_routing_text,
    weather_options,
)
from src.play_tools import draw_cards, format_dice_result, roll_dice

GAME_LIGHTHOUSE = "lighthouse"

ShortcutKind = Literal["draw", "roll_draw", "static", "rag_only"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "order_of_play", "label": "Order of play", "kind": "static"},
    {"id": "weather", "label": "Weather moods", "kind": "static"},
    {"id": "task_routing", "label": "Choose a task (night mood)", "kind": "static"},
    {"id": "light_lamp", "label": "Light the lamp (coin + card)", "kind": "draw"},
    {"id": "maintenance", "label": "Maintenance (d6 + card)", "kind": "roll_draw"},
    {"id": "observation", "label": "Observation (d6 + card)", "kind": "roll_draw"},
    {"id": "event", "label": "Event (flip card)", "kind": "draw"},
    {"id": "beachcombing", "label": "Beachcombing (hour ÷ 2 cards)", "kind": "draw"},
    {"id": "end_watch", "label": "End watch", "kind": "static"},
    {"id": "rules_help", "label": "Lighthouse rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_lighthouse_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(p in lower for p in ("light the lamp", "lighting the light", "light lamp")):
        return "light_lamp"
    if "maintenance" in lower:
        return "maintenance"
    if "observation" in lower or "observe tonight" in lower:
        return "observation"
    if "event" in lower and "lighthouse" in lower:
        return "event"
    if "beachcomb" in lower or "spacecomb" in lower:
        return "beachcombing"
    if "weather" in lower and ("mood" in lower or "feeling" in lower):
        return "weather"
    if "end watch" in lower or "end the night" in lower:
        return "end_watch"
    if "order of play" in lower or "how to play lighthouse" in lower:
        return "order_of_play"
    if "choose a task" in lower or "task routing" in lower:
        return "task_routing"
    if "lighthouse rules" in lower or "keeper duties" in lower:
        return "rules_help"
    return None


def _draw(game_id: str, char_id: str | None, card_source: str, count: int = 1) -> list[str]:
    if card_source == "physical":
        raise ValueError("Physical deck mode: report your card in chat or use virtual deck.")
    result = draw_cards(count=count, game_id=game_id, char_id=char_id)
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    return list(result.get("cards") or [])


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_LIGHTHOUSE,
    char_id: str | None = None,
    card_source: str = "virtual",
    weather_mood: str = "",
    beachcombing_hour: int | None = None,
    cards: list[str] | None = None,
) -> dict:
    if shortcut_id == "order_of_play":
        msg = order_of_play_text()
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "weather":
        lines = ["**The weather (p.8)** — choose a mood for tonight:", ""]
        for w in weather_options():
            lines.append(f"- **{w['label']}** — {w['description']}")
        msg = "\n".join(lines)
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "task_routing":
        msg = task_routing_text()
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "end_watch":
        msg = ending_text()
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "rules_help":
        prompt = (
            "Explain how to play The Lighthouse at the Edge of the Universe solo journaling game: "
            "setup (initial observations, weather, lighting the lamp), choosing tasks, logbook, "
            "and ending the watch. Cite the rulebook when possible."
        )
        return {"user_message": "**Lighthouse rules**", "prompt": prompt}

    if shortcut_id == "light_lamp":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        coin = flip_coin()
        result = format_light_lamp(card, coin)
        user = f"**Light the lamp:** {coin['summary']} · {card}\n\n{result['message']}"
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": [card],
            "coin": coin,
            "lamp_lit": result["lit"],
            "task": "light_lamp",
        }

    if shortcut_id == "maintenance":
        roll = roll_dice("d6")
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        total = int(roll.get("total", 1) or 1)
        fmt = format_maintenance(total, card)
        user = (
            f"**Maintenance:** {format_dice_result(roll)} · {card}\n\n"
            f"**Task:** {fmt['task']}\n\n**Outcome:** {fmt['outcome']}"
        )
        prompt = (
            f"Lighthouse maintenance journal prompt. "
            f"d6={total}, card={card} ({fmt['suit']}). Task: {fmt['task']}. Outcome: {fmt['outcome']}. "
            f"Briefly suggest how to journal this in the logbook."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "cards": [card],
            "dice": roll,
            "task": "maintenance",
            "draw_result": fmt,
        }

    if shortcut_id == "observation":
        roll = roll_dice("d6")
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        total = int(roll.get("total", 1) or 1)
        fmt = format_observation(total, card)
        user = (
            f"**Observation:** {format_dice_result(roll)} · {card}\n\n"
            f"**You see:** {fmt['subject']}\n\n**Distance:** {fmt['distance']}"
        )
        prompt = (
            f"Lighthouse observation journal prompt. d6={total}, card={card}. "
            f"Subject: {fmt['subject']}. Distance: {fmt['distance']}. "
            f"Suggest logbook questions for ships, wildlife, or phenomena."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "cards": [card],
            "dice": roll,
            "task": "observation",
            "draw_result": fmt,
        }

    if shortcut_id == "event":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        fmt = format_event(card)
        user = (
            f"**Event:** {card}\n\n"
            f"**Severity ({fmt.get('color', '')}):** {fmt.get('severity', '')}\n\n"
            f"**Event:** {fmt.get('event', '')}"
        )
        prompt = (
            f"Lighthouse event. Card {card}, {fmt.get('color')} severity: {fmt.get('severity')}. "
            f"Event: {fmt.get('event')}. Journal prompt for the logbook."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "cards": [card],
            "task": "event",
            "draw_result": fmt,
        }

    if shortcut_id == "beachcombing":
        hour = beachcombing_hour if beachcombing_hour is not None else datetime.now().hour
        count = beachcombing_card_count(hour)
        drawn = cards or _draw(game_id, char_id, card_source, count)
        finds = []
        lines = [f"**Beachcombing** (hour {hour} → {count} object(s))", ""]
        for card in drawn:
            coin = flip_coin()
            fmt = format_beachcombing_find(card, coin)
            finds.append(fmt)
            lines.append(
                f"- **{card}** · {coin['summary']}\n  {fmt['item']}\n  _{fmt['source']}_"
            )
        user = "\n".join(lines)
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": drawn,
            "task": "beachcombing",
            "finds": finds,
        }

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
