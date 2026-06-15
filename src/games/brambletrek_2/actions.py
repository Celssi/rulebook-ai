"""Brambletrek 2 sidebar shortcuts."""

from __future__ import annotations

from typing import Literal, TypedDict

from src.games.brambletrek_2.character import get_legacy_options
from src.games.brambletrek_2.curated import (
    combat_reference_summary,
    format_arrival_draw,
    format_combat_setup_curated,
    format_exploration_events,
    format_hollow_event,
    format_item_draw,
    format_overcome_odds,
    format_recovery_draw,
    legacy_by_roll,
    legacy_id_by_roll,
    lookup_hollow_entry,
)
from src.play_tools import draw_cards, format_card_result, format_dice_result, roll_dice

GAME_BRAMBLETREK_2 = "brambletrek_2"

ShortcutKind = Literal["card_rag", "multi_draw_rag", "roll_rag", "rag_only", "static", "multi_draw"]

MULTI_DRAW_SHORTCUTS = frozenset(
    {
        "exploration_day",
        "combat_setup",
        "overcome_odds",
        "hollow_enter",
        "hollow_flip",
        "hollow_escape_attempt",
    }
)


class Brambletrek2Shortcut(TypedDict):
    id: str
    label: str
    kind: ShortcutKind


def match_brambletrek_2_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(p in lower for p in ("how to start", "how do i start", "getting started")):
        return "start_playing"
    if any(
        p in lower
        for p in (
            "exploration day",
            "journey day",
            "today's exploration",
            "todays exploration",
            "four cards",
            "4 cards",
            "cards for today",
            "start my journey",
            "woods day",
        )
    ):
        return "exploration_day"
    if any(p in lower for p in ("combat setup", "start combat", "initiative", "tactic cards")):
        return "combat_setup"
    if "overcome the odds" in lower or ("ability" in lower and "outcome" in lower):
        return "overcome_odds"
    if any(p in lower for p in ("health recovery", "recover health")):
        return "recovery_health"
    if any(p in lower for p in ("morale recovery", "recover morale")):
        return "recovery_morale"
    if any(p in lower for p in ("supplies recovery", "recover supplies")):
        return "recovery_supplies"
    if any(p in lower for p in ("item draw", "draw item", "item table")):
        return "item_draw"
    if any(p in lower for p in ("how did i get here", "arrival", "how do i get here")):
        return "how_did_i_get_here"
    if any(p in lower for p in ("enter hollow", "misty hollow", "hollow enter")):
        return "hollow_enter"
    if any(p in lower for p in ("hollow flip", "flip hollow", "move in hollow")):
        return "hollow_flip"
    if any(p in lower for p in ("escape hollow", "hollow escape", "leave hollow")):
        return "hollow_escape_attempt"
    if "random legacy" in lower or "pick a legacy" in lower:
        return "random_legacy"
    if "legacy overview" in lower or "list legacies" in lower:
        return "legacy_overview"
    return None


BRAMBLETREK_2_SHORTCUTS: list[Brambletrek2Shortcut] = [
    {"id": "start_playing", "label": "How to start playing", "kind": "rag_only"},
    {"id": "exploration_day", "label": "Exploration day (4 cards)", "kind": "multi_draw_rag"},
    {"id": "combat_setup", "label": "Combat setup", "kind": "multi_draw_rag"},
    {"id": "overcome_odds", "label": "Overcome the odds", "kind": "multi_draw_rag"},
    {"id": "recovery_health", "label": "Health recovery", "kind": "card_rag"},
    {"id": "recovery_morale", "label": "Morale recovery", "kind": "card_rag"},
    {"id": "recovery_supplies", "label": "Supplies recovery", "kind": "card_rag"},
    {"id": "item_draw", "label": "Item draw", "kind": "card_rag"},
    {"id": "how_did_i_get_here", "label": "How did I get here?", "kind": "card_rag"},
    {"id": "hollow_enter", "label": "Enter Misty Hollow", "kind": "multi_draw"},
    {"id": "hollow_flip", "label": "Hollow — flip card", "kind": "card_rag"},
    {"id": "hollow_escape_attempt", "label": "Hollow — escape attempt", "kind": "multi_draw"},
    {"id": "random_legacy", "label": "Random Legacy", "kind": "roll_rag"},
    {"id": "legacy_overview", "label": "Legacy overview", "kind": "rag_only"},
]


def shortcuts_for_character(**_filters) -> list[Brambletrek2Shortcut]:
    return list(BRAMBLETREK_2_SHORTCUTS)


def _draw_lines(
    game_id: str,
    count: int,
    labels: list[str],
    *,
    char_id: str | None = None,
    card_source: str = "virtual",
) -> tuple[list[str], str]:
    if card_source == "physical":
        label_str = ", ".join(labels)
        msg = (
            f"**Physical deck** — draw {count} card(s) from your deck "
            f"({label_str}) and report each card."
        )
        return [], msg
    result = draw_cards(count=count, game_id=game_id, char_id=char_id)
    if not result.get("ok"):
        return [], format_card_result(result)
    cards = result["cards"]
    lines = [format_card_result(result)]
    for label, card in zip(labels, cards):
        lines.append(f"- **{label}:** {card}")
    return cards, "\n".join(lines)


def _table_lookup_prompt(
    title: str,
    section: str,
    cards: list[str],
    labels: list[str],
    *,
    extra: str = "",
) -> str:
    card_lines = "\n".join(f"- {label}: {card}" for label, card in zip(labels, cards))
    body = (
        f"Brambletrek 2 — {title} ({section}).\n"
        f"Drawn cards:\n{card_lines}\n"
        "Use the indexed rulebook for table meanings. "
        "Do not say tables are missing."
    )
    if extra:
        body += f"\n{extra}"
    return body


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_BRAMBLETREK_2,
    legacy: str = "",
    char_id: str | None = None,
    card_source: str = "virtual",
    in_hollow: bool = False,
    hollow_row: int | None = None,
    hollow_col: int | None = None,
) -> dict:
    draw_kw = {"char_id": char_id, "card_source": card_source}
    leg_label = get_legacy_options().get(legacy, {}).get("label", legacy)

    if shortcut_id == "start_playing":
        msg = (
            "**How to start Brambletrek 2**\n\n"
            "1. Settings → Character: pick a **Legacy** (Pooh friends or Gnawborn carryover).\n"
            "2. Optionally draw **How did I get here?**\n"
            "3. Each day: **Exploration day** — 4 cards (red=favourable, black=unfortunate).\n"
            "4. Combat, recovery, items, and Misty Hollow use the shortcuts panel."
        )
        return {"user_message": msg, "prompt": msg, "kind": "static", "static": True}

    if shortcut_id == "legacy_overview":
        lines = ["**Legacies** (BT2 pp. 18–33):"]
        for lid, meta in get_legacy_options().items():
            if lid:
                lines.append(f"- **{meta['label']}** — {meta.get('tagline', '')}")
        text = "\n".join(lines)
        return {"user_message": text, "prompt": text, "kind": "rag_only"}

    if shortcut_id == "exploration_day":
        cards, deck_block = _draw_lines(
            game_id, 4, ["Event 1", "Event 2", "Event 3", "Event 4"], **draw_kw
        )
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "multi_draw_rag"}
        curated = format_exploration_events(cards)
        prompt = _table_lookup_prompt(
            "Exploration day",
            "Exploration Tables pp. 35–38",
            cards,
            ["Event 1", "Event 2", "Event 3", "Event 4"],
            extra="Narrate each event; apply stats when the player resolves them in the panel.",
        )
        user = f"**Exploration day** — four cards for the Woods.\n\n{deck_block}\n\n{curated}"
        return {
            "user_message": user,
            "prompt": prompt,
            "kind": "multi_draw_rag",
            "exploration_cards": cards,
        }

    if shortcut_id == "combat_setup":
        cards, deck_block = _draw_lines(
            game_id,
            7,
            ["Opponent", "Your initiative", "Opponent initiative", "T1", "T2", "T3", "T4"],
            **draw_kw,
        )
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "multi_draw_rag"}
        curated = format_combat_setup_curated(cards, legacy_id=legacy, legacy_label=leg_label)
        ref = combat_reference_summary()
        prompt = _table_lookup_prompt(
            "Combat setup",
            "Combat & Encounters pp. 51–59",
            cards,
            ["Opponent", "Initiative you", "Initiative foe", "T1", "T2", "T3", "T4"],
            extra="Explain initiative, opponent, and each tactic in plain language.",
        )
        user = f"**Combat setup**\n\n{deck_block}\n\n{curated}\n\n{ref}"
        return {"user_message": user, "prompt": prompt, "kind": "multi_draw_rag"}

    if shortcut_id == "overcome_odds":
        cards, deck_block = _draw_lines(game_id, 2, ["Ability", "Outcome"], **draw_kw)
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "multi_draw_rag"}
        cmp = format_overcome_odds(cards[0], cards[1])
        prompt = _table_lookup_prompt(
            "Overcome the Odds",
            "p. 14",
            cards,
            ["Ability", "Outcome"],
            extra="Ace=critical success, 2=critical failure.",
        )
        user = f"**Overcome the odds**\n\n{deck_block}\n\n{cmp}"
        return {"user_message": user, "prompt": prompt, "kind": "multi_draw_rag"}

    if shortcut_id in ("recovery_health", "recovery_morale", "recovery_supplies"):
        stat = shortcut_id.replace("recovery_", "")
        cards, deck_block = _draw_lines(game_id, 1, [stat.title()], **draw_kw)
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "card_rag"}
        curated = format_recovery_draw(stat, cards[0])
        prompt = _table_lookup_prompt(
            f"{stat.title()} recovery",
            "p. 13",
            cards,
            [stat.title()],
        )
        user = f"**{stat.title()} recovery**\n\n{deck_block}\n\n{curated}"
        return {"user_message": user, "prompt": prompt, "kind": "card_rag"}

    if shortcut_id == "item_draw":
        cards, deck_block = _draw_lines(game_id, 1, ["Item"], **draw_kw)
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "card_rag"}
        curated = format_item_draw(cards[0])
        prompt = _table_lookup_prompt("Item table", "p. 39", cards, ["Item"])
        user = f"**Item draw**\n\n{deck_block}\n\n{curated}"
        return {"user_message": user, "prompt": prompt, "kind": "card_rag"}

    if shortcut_id == "how_did_i_get_here":
        cards, deck_block = _draw_lines(game_id, 1, ["Arrival"], **draw_kw)
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "card_rag"}
        curated = format_arrival_draw(cards[0])
        user = f"**How did I get here?**\n\n{deck_block}\n\n{curated}"
        return {
            "user_message": user,
            "prompt": user,
            "kind": "card_rag",
            "arrival_card": cards[0],
        }

    if shortcut_id == "hollow_enter":
        cards, deck_block = _draw_lines(
            game_id, 21, ["Entry"] + [f"Grid {i}" for i in range(1, 21)], **draw_kw
        )
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "multi_draw"}
        entry_card = cards[0]
        grid_cards = cards[1:21]
        entry = lookup_hollow_entry(entry_card)
        entry_prompt = entry.get("label", "") if entry else ""
        user = (
            f"**Enter Misty Hollow**\n\n{deck_block}\n\n"
            f"Entry prompt: **{entry_prompt or entry_card}**\n"
            "_5×4 grid dealt; use Hollow panel to navigate._"
        )
        return {
            "user_message": user,
            "prompt": user,
            "kind": "multi_draw",
            "hollow_entry_card": entry_card,
            "hollow_grid_cards": grid_cards,
            "hollow_entry_prompt": entry_prompt,
        }

    if shortcut_id == "hollow_flip":
        cards, deck_block = _draw_lines(game_id, 1, ["Hollow cell"], **draw_kw)
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "card_rag"}
        curated = format_hollow_event(cards[0])
        user = f"**Hollow flip** @ ({hollow_row},{hollow_col})\n\n{deck_block}\n\n{curated}"
        return {
            "user_message": user,
            "prompt": user,
            "kind": "card_rag",
            "hollow_card": cards[0],
            "hollow_row": hollow_row,
            "hollow_col": hollow_col,
        }

    if shortcut_id == "hollow_escape_attempt":
        cards, deck_block = _draw_lines(
            game_id, 2, ["Anchor test", "Exit prompt"], **draw_kw
        )
        if not cards:
            return {"user_message": deck_block, "prompt": deck_block, "kind": "multi_draw"}
        anchor, exit_card = cards[0], cards[1]
        from src.games.brambletrek_2.curated import lookup_hollow_exit, parse_playing_card

        ap = parse_playing_card(anchor)
        test = "peaceful release" if ap and ap["suit"] in ("hearts", "diamonds") else "Hollow clings (−5 Health)"
        exit_row = lookup_hollow_exit(exit_card)
        user = (
            f"**Hollow escape**\n\n{deck_block}\n\n"
            f"Anchor: {anchor} → {test}\n"
            f"Exit prompt: {exit_row.get('label', exit_card) if exit_row else exit_card}"
        )
        return {"user_message": user, "prompt": user, "kind": "multi_draw", "escape_cards": cards}

    if shortcut_id == "random_legacy":
        roll = roll_dice("1d16")
        total = int(roll.get("total", 1))
        lid = legacy_id_by_roll(total)
        label = legacy_by_roll(total)
        dice_block = format_dice_result(roll)
        prompt = (
            f"Brambletrek 2 random Legacy: rolled {total} → **{label}** ({lid}). "
            "Summarize starting stats and abilities from the rulebook."
        )
        user = f"**Random Legacy**\n\n{dice_block}\n\n→ **{label}**"
        return {"user_message": user, "prompt": prompt, "kind": "roll_rag"}

    return {
        "user_message": f"Unknown shortcut: {shortcut_id}",
        "prompt": shortcut_id,
        "kind": "rag_only",
    }
