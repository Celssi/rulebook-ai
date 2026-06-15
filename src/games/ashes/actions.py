"""Ashes sidebar shortcuts."""

from __future__ import annotations

from typing import Literal, TypedDict

from src.games.ashes.curated import (
    ember_for_level,
    format_character_gift_draw,
    format_enemy_draw,
    format_journal_draw,
    format_room_draw,
    format_trial_draw,
    format_trials_draw,
    lookup_armour,
    lookup_starting_weapon,
)
from src.play_tools import draw_cards, format_dice_result, roll_dice

GAME_ASHES = "ashes"

ShortcutKind = Literal["multi_draw", "roll", "static", "rag_only", "card_draw"]

MULTI_DRAW_SHORTCUTS = frozenset({"draw_room_journal", "character_setup", "draw_starting_trials"})


class AshesShortcut(TypedDict):
    id: str
    label: str
    kind: ShortcutKind
    group: str


SHORTCUTS: list[AshesShortcut] = [
    {"id": "draw_room", "label": "Draw room card", "kind": "card_draw", "group": "dungeon"},
    {"id": "draw_journal", "label": "Draw journal prompt", "kind": "card_draw", "group": "dungeon"},
    {"id": "draw_room_journal", "label": "Draw room + journal", "kind": "multi_draw", "group": "dungeon"},
    {"id": "draw_enemy", "label": "Draw enemy", "kind": "card_draw", "group": "dungeon"},
    {"id": "sanctuary_check", "label": "Sanctuary check (d6)", "kind": "roll", "group": "dungeon"},
    {"id": "navigate", "label": "Navigation (d6)", "kind": "roll", "group": "dungeon"},
    {"id": "boss_entry", "label": "Boss entry roll (d6)", "kind": "roll", "group": "dungeon"},
    {"id": "roll_trap", "label": "Trap table (2d6)", "kind": "roll", "group": "tables"},
    {"id": "roll_loot", "label": "Loot table (2d6)", "kind": "roll", "group": "tables"},
    {"id": "draw_starting_trials", "label": "Draw 4 starting trials", "kind": "multi_draw", "group": "trials"},
    {"id": "draw_trial", "label": "Draw new trial", "kind": "card_draw", "group": "trials"},
    {"id": "trials_help", "label": "Trials & Ember rules", "kind": "rag_only", "group": "trials"},
    {"id": "ember_help", "label": "Level up & Ember cost", "kind": "static", "group": "trials"},
    {"id": "character_gift", "label": "Draw Fate's Gift", "kind": "card_draw", "group": "character"},
    {"id": "character_armour", "label": "Roll starting armour (d6)", "kind": "roll", "group": "character"},
    {"id": "character_setup", "label": "Character setup (gift + armour)", "kind": "multi_draw", "group": "character"},
    {"id": "roll_melee_weapon", "label": "Roll melee weapon (d6)", "kind": "roll", "group": "character"},
    {"id": "roll_ranged_weapon", "label": "Roll ranged weapon (d6)", "kind": "roll", "group": "character"},
    {"id": "dungeon_rules", "label": "Dungeon layout rules", "kind": "rag_only", "group": "rules"},
    {"id": "checks_help", "label": "Checks & throws", "kind": "rag_only", "group": "rules"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def shortcuts_for_scion(**_kwargs) -> list[AshesShortcut]:
    return list(SHORTCUTS)


def match_ashes_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(p in lower for p in ("draw room", "room card", "next room", "generate room")):
        if "journal" in lower or "prompt" in lower:
            return "draw_room_journal"
        return "draw_room"
    if any(p in lower for p in ("journal prompt", "journaling prompt", "draw journal", "flavour card")):
        return "draw_journal"
    if any(p in lower for p in ("draw enemy", "enemy encounter", "ambush enemy", "roll enemy")):
        return "draw_enemy"
    if "sanctuary" in lower and ("check" in lower or "roll" in lower):
        return "sanctuary_check"
    if any(p in lower for p in ("navigation", "turn left", "turn right", "which direction")):
        return "navigate"
    if "boss" in lower and ("entry" in lower or "room" in lower):
        return "boss_entry"
    if "trap table" in lower or "roll trap" in lower:
        return "roll_trap"
    if "loot table" in lower or "roll loot" in lower or "standard loot" in lower:
        return "roll_loot"
    if "starting trials" in lower or "draw 4 trials" in lower or "four trials" in lower:
        return "draw_starting_trials"
    if "new trial" in lower or "draw trial" in lower:
        return "draw_trial"
    if "trial" in lower and ("ember" in lower or "rules" in lower):
        return "trials_help"
    if "ember" in lower and ("level" in lower or "cost" in lower):
        return "ember_help"
    if "fate" in lower and "gift" in lower:
        return "character_gift"
    if "armour" in lower or "armor" in lower:
        if "roll" in lower or "starting" in lower:
            return "character_armour"
    if "melee weapon" in lower:
        return "roll_melee_weapon"
    if "ranged weapon" in lower or "bow" in lower:
        return "roll_ranged_weapon"
    if "character setup" in lower or "create scion" in lower:
        return "character_setup"
    if "dungeon layout" in lower or "room generation" in lower:
        return "dungeon_rules"
    if "check" in lower and ("throw" in lower or "difficulty" in lower or "3d6" in lower):
        return "checks_help"
    return None


def _card_label(card: str) -> str:
    return f"**{card}**"


def _draw(game_id: str, char_id: str | None, card_source: str, count: int) -> list[str]:
    if card_source == "physical":
        raise ValueError("Physical deck mode: report your cards in chat or switch to virtual deck.")
    result = draw_cards(count=count, game_id=game_id, char_id=char_id)
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    return list(result.get("cards") or [])


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_ASHES,
    char_id: str | None = None,
    card_source: str = "virtual",
    prompt_set: str = "crypt",
    level: int = 1,
    cards: list[str] | None = None,
    combat_room: bool = False,
) -> dict:
    if shortcut_id == "draw_room":
        drawn = cards or _draw(game_id, char_id, card_source, 1)
        room = format_room_draw(drawn[0])
        user = (
            f"**Room draw:** {_card_label(drawn[0])}\n\n"
            f"**{room['room']}** · Check: {room['check']}\n"
            f"**{room['suit_label']}** — {room['suit_feature']}: {room['suit_detail']}"
        )
        if room.get("spades_extra_enemy"):
            user += "\n\n*Spades + combat room: add one extra enemy.*"
        prompt = (
            f"Ashes room generation. Card {drawn[0]}: room {room['room']}, check {room['check']}. "
            f"Suit {room['suit_label']}: {room['suit_feature']} — {room['suit_detail']}. "
            "Explain how to resolve this room and journal it."
        )
        return {"user_message": user, "prompt": prompt, "draw_result": room, "cards": drawn}

    if shortcut_id == "draw_journal":
        drawn = cards or _draw(game_id, char_id, card_source, 1)
        journal = format_journal_draw(drawn[0], prompt_set=prompt_set)
        user = (
            f"**Journal prompt:** {_card_label(drawn[0])} ({journal['suit_label']}) "
            f"[{journal.get('prompt_set', prompt_set)}]\n\n"
            f"{journal['event']}\n\n**Check:** {journal['check']}"
        )
        if journal.get("suit_note"):
            user += f"\n\n*{journal['suit_note']}*"
        prompt = (
            f"Ashes journaling prompt ({journal.get('prompt_set', prompt_set)}) for {journal['suit_label']} {drawn[0]}: "
            f"{journal['event']} Check: {journal['check']}. "
            "Write evocative arrival prose before the room's main feature resolves."
        )
        return {"user_message": user, "prompt": prompt, "draw_result": journal, "cards": drawn}

    if shortcut_id == "draw_room_journal":
        drawn = cards or _draw(game_id, char_id, card_source, 2)
        room = format_room_draw(drawn[0])
        journal = format_journal_draw(drawn[1], prompt_set=prompt_set)
        user = (
            f"**Room:** {_card_label(drawn[0])} — **{room['room']}** ({room['check']})\n"
            f"**Journal:** {_card_label(drawn[1])} — {journal['event']} ({journal['check']})"
        )
        prompt = (
            f"Ashes room+journal ({journal.get('prompt_set', prompt_set)}). Room card {drawn[0]}: {room['room']} ({room['check']}), "
            f"suit feature {room['suit_feature']}. Journal card {drawn[1]} ({journal['suit_label']}): "
            f"{journal['event']}. Narrate arriving at the room with the journal prompt first."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "draw_result": {"room": room, "journal": journal},
            "cards": drawn,
        }

    if shortcut_id == "draw_enemy":
        drawn = cards or _draw(game_id, char_id, card_source, 1)
        enemy = format_enemy_draw(drawn[0])
        user = f"**Enemy draw:** {_card_label(drawn[0])}\n\n**{enemy['enemy']}**"
        prompt = (
            f"Ashes enemy encounter table: {drawn[0]} = {enemy['enemy']}. "
            "Summarize this enemy's role in combat from the rules."
        )
        return {"user_message": user, "prompt": prompt, "draw_result": enemy, "cards": drawn}

    if shortcut_id == "draw_starting_trials":
        drawn = cards or _draw(game_id, char_id, card_source, 4)
        batch = format_trials_draw(drawn)
        lines = []
        for t in batch["trials"]:
            lines.append(f"- {_card_label(t['card'])} ({t['color']}): {t['trial']}")
        user = "**Starting trials (4 cards):**\n\n" + "\n".join(lines)
        return {
            "user_message": user,
            "prompt": user,
            "draw_result": batch,
            "cards": drawn,
            "static": True,
            "replace_trials": True,
        }

    if shortcut_id == "draw_trial":
        drawn = cards or _draw(game_id, char_id, card_source, 1)
        trial = format_trial_draw(drawn[0])
        user = (
            f"**New trial:** {_card_label(drawn[0])} ({trial['color']})\n\n{trial['trial']}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "draw_result": trial,
            "cards": drawn,
            "static": True,
            "append_trial": True,
        }

    if shortcut_id == "sanctuary_check":
        result = roll_dice("d6")
        val = int(result["rolls"][0])
        if combat_room:
            success = val >= 4
            threshold = "4–6 after combat"
        else:
            success = val >= 5
            threshold = "5–6 after non-combat room"
        msg = (
            f"**Sanctuary check:** {format_dice_result(result)} — "
            f"{'Sanctuary!' if success else 'Not a sanctuary'} ({threshold})"
        )
        if success:
            msg += "\n\n*Full heal, restore potions/gift uses, may level up with Ember.*"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result, "is_sanctuary": success}

    if shortcut_id == "navigate":
        result = roll_dice("d6")
        val = int(result["rolls"][0])
        if val <= 2:
            direction = "Turn left"
        elif val <= 4:
            direction = "Continue straight"
        else:
            direction = "Turn right"
        msg = f"**Navigation:** {format_dice_result(result)} — **{direction}**"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result}

    if shortcut_id == "boss_entry":
        result = roll_dice("d6")
        val = int(result["rolls"][0])
        success = val >= 5
        msg = (
            f"**Boss entry:** {format_dice_result(result)} — "
            f"{'May enter boss room!' if success else 'Draw another room first'} "
            "(needs 10+ rooms cleared, 3 open directions; 5–6 to enter)"
        )
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result}

    if shortcut_id == "roll_trap":
        result = roll_dice("2d6")
        total = int(result["total"])
        from src.games.ashes.curated import lookup_trap

        trap = lookup_trap(total)
        msg = f"**Trap table:** {format_dice_result(result)} — {trap or 'No entry'}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result}

    if shortcut_id == "roll_loot":
        result = roll_dice("2d6")
        total = int(result["total"])
        from src.games.ashes.curated import lookup_loot

        loot = lookup_loot(total)
        msg = f"**Loot table:** {format_dice_result(result)} — {loot or 'Reroll 1s on d6 variant'}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result}

    if shortcut_id == "character_gift":
        drawn = cards or _draw(game_id, char_id, card_source, 1)
        gift = format_character_gift_draw(drawn[0])
        user = f"**Fate's Gift:** {_card_label(drawn[0])}\n\n{gift['gift']}"
        return {"user_message": user, "prompt": user, "draw_result": gift, "cards": drawn, "static": True}

    if shortcut_id == "character_armour":
        result = roll_dice("d6")
        val = int(result["rolls"][0])
        armour = lookup_armour(val)
        msg = f"**Starting armour:** {format_dice_result(result)}\n\n{armour}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result, "armour_roll": val}

    if shortcut_id == "character_setup":
        drawn = cards or _draw(game_id, char_id, card_source, 1)
        gift = format_character_gift_draw(drawn[0])
        armour_roll = roll_dice("d6")
        val = int(armour_roll["rolls"][0])
        armour = lookup_armour(val)
        user = (
            f"**Fate's Gift:** {_card_label(drawn[0])}\n{gift['gift']}\n\n"
            f"**Armour:** {format_dice_result(armour_roll)}\n{armour}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "cards": drawn,
            "draw_result": {"gift": gift, "armour": armour, "armour_roll": val},
            "dice": armour_roll,
        }

    if shortcut_id == "roll_melee_weapon":
        result = roll_dice("d6")
        val = int(result["rolls"][0])
        weapon = lookup_starting_weapon("melee", val)
        msg = f"**Melee weapon:** {format_dice_result(result)}\n\n{weapon}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result, "weapon_kind": "melee", "weapon": weapon}

    if shortcut_id == "roll_ranged_weapon":
        result = roll_dice("d6")
        val = int(result["rolls"][0])
        weapon = lookup_starting_weapon("ranged", val)
        msg = f"**Ranged weapon:** {format_dice_result(result)}\n\n{weapon}"
        return {"user_message": msg, "prompt": msg, "static": True, "dice": result, "weapon_kind": "ranged", "weapon": weapon}

    if shortcut_id == "ember_help":
        need = ember_for_level(level)
        msg = f"**Ember to level up from Lv {level}:** {need} Ember (formula: 1 + 2 × current level). Complete trials for +1 Ember each."
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "dungeon_rules":
        prompt = (
            "Explain Ashes dungeon layout: draw a card per room step, suit sets secondary "
            "journal feature (Hearts allies/healing, Diamonds treasure, Clubs traps, Spades hidden enemy). "
            "Card rank sets primary room from the room table. After completing a room, sanctuary d6 and navigation d6. "
            "Boss entry after 10+ rooms with 3 open directions."
        )
        return {"user_message": "**Dungeon layout rules**", "prompt": prompt}

    if shortcut_id == "checks_help":
        prompt = (
            "Explain Ashes checks and throws: 3d6 roll-over vs target 18 minus stat; "
            "PWR/INT/AGL; advantage/disadvantage; failing room checks use the consequence table."
        )
        return {"user_message": "**Checks & throws**", "prompt": prompt}

    if shortcut_id == "trials_help":
        prompt = (
            "Explain Ashes Trials: draw 4 at dungeon start (max 10 active). Hearts/Diamonds = red trial table, "
            "Clubs/Spades = black. Completing a trial grants 1 Ember. Level up at Sanctuary spending Ember."
        )
        return {"user_message": "**Trials & Ember**", "prompt": prompt}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
