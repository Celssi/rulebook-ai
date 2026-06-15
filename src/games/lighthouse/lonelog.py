"""Lighthouse Lonelog formatters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.lighthouse.play import get_lighthouse_store
from src.games.saves.lonelog import card_short_label, format_draw, format_mechanical, format_narrative, format_scene

if TYPE_CHECKING:
    from src.games.lighthouse.watch import KeeperWatch


def format_night_header(watch: KeeperWatch) -> str:
    return format_scene(watch.night_count, f"Lighthouse watch, Night {watch.night_count}")


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    return get_lighthouse_store().read_log_tail(slot_id, n_lines)


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
    return (
        "Story so far at the lighthouse (chronological; continue naturally):\n\n" + body
    )


def log_task_draw(slot_id: str, label: str, cards: list[str]) -> None:
    store = get_lighthouse_store()
    short = [card_short_label(c) for c in cards]
    store.append_log(slot_id, format_draw(short, label=label))


def log_narrative_line(slot_id: str, text: str) -> None:
    get_lighthouse_store().append_log(slot_id, format_narrative(text))


def log_mechanical_line(slot_id: str, text: str) -> None:
    get_lighthouse_store().append_log(slot_id, format_mechanical(text))


def open_night(slot_id: str, watch: KeeperWatch) -> None:
    store = get_lighthouse_store()
    store.append_log(slot_id, "")
    store.append_log(slot_id, format_night_header(watch))
