"""Colostle shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.colostle.curated import (
    class_options,
    format_character_draw,
    format_exploration_draw,
    format_person_opponent,
    format_rook_opponent,
    lookup_battlements,
    lookup_city,
    lookup_event,
    lookup_exposure,
    lookup_item,
    lookup_npc,
    lookup_ocean,
    lookup_ocean_weather,
    lookup_oracle,
    lookup_rookling,
    lookup_storytelling,
    lookup_hunters_guild,
)
from src.play_tools import draw_cards, format_dice_result, roll_dice

GAME_COLOSTLE = "colostle"

ShortcutKind = Literal[
    "multi_draw",
    "draw",
    "static",
    "rag_only",
    "roll",
]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "draw_character", "label": "Draw Calling & Nature", "kind": "multi_draw"},
    {"id": "exploration_phase", "label": "Exploration phase", "kind": "multi_draw"},
    {"id": "draw_item", "label": "Item table", "kind": "draw"},
    {"id": "draw_event", "label": "Event table", "kind": "draw"},
    {"id": "oracle", "label": "Oracle (yes/no)", "kind": "draw"},
    {"id": "storytelling", "label": "Storytelling prompt", "kind": "draw"},
    {"id": "npc", "label": "NPC generator", "kind": "draw"},
    {"id": "ocean_encounter", "label": "Ocean encounter", "kind": "draw"},
    {"id": "ocean_weather", "label": "Ocean weather", "kind": "draw"},
    {"id": "city_amenity", "label": "City amenity", "kind": "draw"},
    {"id": "hunters_guild", "label": "Hunter's Guild quest", "kind": "multi_draw"},
    {"id": "rookling_creche", "label": "Rookling Crèche", "kind": "draw"},
    {"id": "battlements", "label": "Battlements encounter", "kind": "draw"},
    {"id": "exposure_event", "label": "Exposure event", "kind": "draw"},
    {"id": "combat_person", "label": "Create human opponent", "kind": "multi_draw"},
    {"id": "combat_rook", "label": "Create Rook opponent", "kind": "multi_draw"},
    {"id": "classes_help", "label": "Character classes", "kind": "static"},
    {"id": "rules_help", "label": "Colostle rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_colostle_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(p in lower for p in ("draw calling", "draw nature", "character creation", "create character")):
        return "draw_character"
    if "exploration phase" in lower or "roomlands exploration" in lower or lower.strip() == "explore":
        return "exploration_phase"
    if "item table" in lower or lower.strip() in ("draw item", "item draw"):
        return "draw_item"
    if "event table" in lower or lower.strip() in ("draw event", "event draw"):
        return "draw_event"
    if "oracle" in lower:
        return "oracle"
    if "storytelling" in lower:
        return "storytelling"
    if "npc" in lower or "generate npc" in lower:
        return "npc"
    if "ocean encounter" in lower or "sea encounter" in lower:
        return "ocean_encounter"
    if "ocean weather" in lower or "sea weather" in lower:
        return "ocean_weather"
    if "city amenity" in lower or "city building" in lower:
        return "city_amenity"
    if "hunter" in lower and "guild" in lower:
        return "hunters_guild"
    if "rookling" in lower and ("crèche" in lower or "creche" in lower or "draw" in lower):
        return "rookling_creche"
    if "battlements" in lower:
        return "battlements"
    if "exposure" in lower:
        return "exposure_event"
    if "human opponent" in lower or "create person opponent" in lower:
        return "combat_person"
    if "rook opponent" in lower or "create rook" in lower:
        return "combat_rook"
    if "character class" in lower or "colostle classes" in lower:
        return "classes_help"
    if "colostle rules" in lower or "how to play colostle" in lower:
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
    game_id: str = GAME_COLOSTLE,
    char_id: str | None = None,
    card_source: str = "virtual",
    exploration_score: int = 3,
    cards: list[str] | None = None,
) -> dict:
    if shortcut_id == "classes_help":
        lines = ["**Character classes (p.16–22):**", ""]
        for c in class_options():
            lines.append(
                f"- **{c['label']}** — Exploration {c['exploration']}, Combat {c['combat']}"
            )
        msg = "\n".join(lines)
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "rules_help":
        prompt = (
            "Explain how to play Colostle solo RPG: character creation (Calling, Nature, Class, Weapon), "
            "exploration phase (draw cards equal to exploration score), combat, journal writing, "
            "and optional modules (Ocean, City, Battlements). Cite the rulebook."
        )
        return {"user_message": "**Colostle rules**", "prompt": prompt}

    if shortcut_id == "draw_character":
        drawn = cards or _draw(game_id, char_id, card_source, 2)
        fmt = format_character_draw(drawn[0], drawn[1])
        user = (
            f"**Character draw:** {drawn[0]} · {drawn[1]}\n\n"
            f"**Calling:** {fmt['calling']}\n\n"
            f"**Nature:** {fmt['nature']}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": drawn,
            "task": "draw_character",
            "draw_result": fmt,
        }

    if shortcut_id == "exploration_phase":
        count = max(1, min(5, int(exploration_score or 3)))
        drawn = cards or _draw(game_id, char_id, card_source, count)
        results = format_exploration_draw(drawn)
        lines = [f"**Exploration phase** ({count} card(s))", ""]
        for card, res in zip(drawn, results):
            lines.append(f"- **{card}** — {res.get('prompt', '')}")
        user = "\n".join(lines)
        prompt = (
            f"Colostle exploration journal. Drew {count} cards: {', '.join(drawn)}. "
            f"Prompts: {'; '.join(r.get('prompt', '') for r in results)}. "
            f"Suggest how to weave these into one journal chapter."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "cards": drawn,
            "task": "exploration_phase",
            "draw_result": results,
        }

    if shortcut_id == "draw_item":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        from src.games.colostle.curated import lookup_item, parse_playing_card

        parsed = parse_playing_card(card)
        item = lookup_item(parsed["rank_key"]) if parsed else ""
        user = f"**Item:** {card}\n\n{item}"
        prompt = (
            f"Colostle item table. Card {card}: {item}. "
            f"Write a journal scene discovering or using this item."
        )
        return {"user_message": user, "prompt": prompt, "cards": [card], "task": "draw_item"}

    if shortcut_id == "draw_event":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        from src.games.colostle.curated import parse_playing_card

        parsed = parse_playing_card(card)
        event = lookup_event(parsed["rank_key"]) if parsed else ""
        user = f"**Event:** {card}\n\n{event}"
        prompt = (
            f"Colostle event table. Card {card}: {event}. "
            f"Write a journal scene for this exploration event."
        )
        return {"user_message": user, "prompt": prompt, "cards": [card], "task": "draw_event"}

    if shortcut_id == "oracle":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        fmt = lookup_oracle(card)
        user = f"**Oracle:** {card} ({fmt.get('color', '')})\n\n**Answer:** {fmt.get('answer', '')}"
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "oracle"}

    if shortcut_id == "storytelling":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        fmt = lookup_storytelling(card)
        user = (
            f"**Storytelling:** {card}\n\n"
            f"**Incite:** {fmt.get('incite', '')}\n"
            f"**Subject:** {fmt.get('subject', '')}\n"
            f"**Twist:** {fmt.get('twist', '')}"
        )
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "storytelling"}

    if shortcut_id == "npc":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        fmt = lookup_npc(card)
        user = (
            f"**NPC:** {card}\n\n"
            f"**{fmt.get('name', '')}** — {fmt.get('look', '')}\n"
            f"_{fmt.get('trait', '')}_"
        )
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "npc"}

    if shortcut_id == "ocean_encounter":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        fmt = lookup_ocean(card)
        user = f"**Ocean encounter:** {card}\n\n{fmt.get('prompt', '')}"
        prompt = f"Colostle ocean encounter. Card {card}: {fmt.get('prompt', '')}. Journal prompt."
        return {"user_message": user, "prompt": prompt, "cards": [card], "task": "ocean_encounter"}

    if shortcut_id == "ocean_weather":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        weather = lookup_ocean_weather(card)
        user = f"**Ocean weather:** {card}\n\n{weather}"
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "ocean_weather"}

    if shortcut_id == "city_amenity":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        amenity = lookup_city(card)
        user = f"**City amenity:** {card}\n\n{amenity}"
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "city_amenity"}

    if shortcut_id == "hunters_guild":
        drawn = cards or _draw(game_id, char_id, card_source, 4)
        fmt = lookup_hunters_guild(drawn)
        if fmt.get("error"):
            raise ValueError(str(fmt["error"]))
        user = (
            f"**Hunter's Guild quest:** {', '.join(drawn)}\n\n"
            f"**Distance:** {fmt['distance']}\n"
            f"**Location:** {fmt['location']}\n"
            f"**Twist:** {fmt['twist']}\n"
            f"**Reward:** {fmt['reward']}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": drawn,
            "task": "hunters_guild",
            "draw_result": fmt,
        }

    if shortcut_id == "rookling_creche":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        rookling = lookup_rookling(card)
        user = f"**Rookling Crèche:** {card}\n\n{rookling}"
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "rookling_creche"}

    if shortcut_id == "battlements":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        fmt = lookup_battlements(card)
        user = f"**Battlements:** {card}\n\n{fmt.get('prompt', '')}"
        prompt = f"Colostle battlements encounter. {card}: {fmt.get('prompt', '')}. Journal prompt."
        return {"user_message": user, "prompt": prompt, "cards": [card], "task": "battlements"}

    if shortcut_id == "exposure_event":
        card = (cards or _draw(game_id, char_id, card_source, 1))[0]
        event = lookup_exposure(card)
        user = f"**Exposure event:** {card}\n\n{event}"
        return {"user_message": user, "prompt": user, "static": True, "cards": [card], "task": "exposure_event"}

    if shortcut_id == "combat_person":
        drawn = cards or _draw(game_id, char_id, card_source, 2)
        fmt = format_person_opponent(drawn[0], drawn[1])
        user = (
            f"**Human opponent:** {drawn[0]} · {drawn[1]}\n\n"
            f"**Intention:** {fmt['intention']}\n"
            f"**Weapon:** {fmt['weapon_type']}\n"
            f"**Combat score:** {fmt['combat_score']}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": drawn,
            "task": "combat_person",
            "draw_result": fmt,
        }

    if shortcut_id == "combat_rook":
        drawn = cards or _draw(game_id, char_id, card_source, 4)
        fmt = format_rook_opponent(drawn[0], drawn[1], drawn[2], drawn[3])
        user = (
            f"**Rook opponent:** {', '.join(drawn)}\n\n"
            f"**Body:** {fmt['body_type']}\n"
            f"**Magic:** {fmt['magic_type']}\n"
            f"**Weapon:** {fmt['weapon_type']}\n"
            f"**Reward:** {fmt['reward']}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": drawn,
            "task": "combat_rook",
            "draw_result": fmt,
        }

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
