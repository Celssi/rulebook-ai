"""Whispers Lonelog formatters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.saves.lonelog import card_short_label, format_draw, format_mechanical, format_scene
from src.games.whispers.play import get_whispers_store

if TYPE_CHECKING:
    from src.games.whispers.investigation import WhispersInvestigation


def format_investigation_header(inv: WhispersInvestigation) -> str:
    loc = inv.location_name.strip() or inv.location_title.strip() or "Unknown location"
    return format_scene(inv.turn_number, f"Whispers — {loc}")


def format_whisper_draw_line(inv: WhispersInvestigation, card: str, table: str) -> str:
    label = table.replace("_", " ").title() if table else "draw"
    return format_draw([card_short_label(card)], label=f"Turn {inv.turn_number} {label}")


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    return get_whispers_store().read_log_tail(slot_id, n_lines)


def narrative_context_for_ai(
    slot_id: str,
    *,
    max_entries: int = 8,
    max_chars: int = 3500,
) -> str:
    if not slot_id.strip():
        return ""
    lines = read_tail(slot_id, n_lines=200)
    snippets: list[str] = []
    for raw in lines:
        ln = raw.strip()
        if not ln or ln.startswith("#") or ln == "_Lonelog session log_":
            continue
        if ln.startswith("=>"):
            text = ln[2:].strip()
            if text:
                snippets.append(text)
        elif ln.startswith("S") and "*" in ln:
            snippets.append(ln)
    if not snippets:
        return ""
    tail = snippets[-max_entries:]
    body = "\n\n".join(tail)
    if len(body) > max_chars:
        body = body[-max_chars:].lstrip()
        cut = body.find("\n\n")
        if 0 <= cut < 200:
            body = body[cut + 2 :]
    return (
        "Story so far in this investigation (continue naturally — do not repeat events):\n\n"
        + body
    )


def log_whisper_draw(slot_id: str, inv: WhispersInvestigation, card: str, table: str) -> None:
    store = get_whispers_store()
    store.append_log(slot_id, format_whisper_draw_line(inv, card, table))


def log_location_draw(slot_id: str, card: str, title: str) -> None:
    store = get_whispers_store()
    store.append_log(slot_id, format_draw([card_short_label(card)], label=f"Location: {title}"))


def log_player_action(slot_id: str, text: str) -> None:
    from src.games.saves.lonelog import format_player_action

    store = get_whispers_store()
    store.append_log(slot_id, format_player_action(text))


def log_narrative(slot_id: str, text: str) -> None:
    from src.games.saves.lonelog import format_narrative

    store = get_whispers_store()
    store.append_log(slot_id, format_narrative(text))


def open_investigation(slot_id: str, inv: WhispersInvestigation) -> None:
    store = get_whispers_store()
    store.append_log(slot_id, "")
    store.append_log(slot_id, format_investigation_header(inv))
