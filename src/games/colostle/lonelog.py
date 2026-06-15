"""Colostle lonelog formatting."""

from __future__ import annotations

from src.games.colostle.play import get_colostle_store
from src.games.saves.lonelog import card_short_label, format_draw, format_narrative


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    return get_colostle_store().read_log_tail(slot_id, n_lines)


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
    if not snippets:
        return ""
    body = "\n\n".join(snippets[-max_entries:])
    if len(body) > max_chars:
        body = body[-max_chars:].lstrip()
    return "Story so far in Colostle (continue naturally):\n\n" + body


def log_draw(slot_id: str, label: str, cards: list[str]) -> None:
    short = [card_short_label(c) for c in cards]
    get_colostle_store().append_log(slot_id, format_draw(short, label=label))


def log_narrative_line(slot_id: str, text: str) -> None:
    get_colostle_store().append_log(slot_id, format_narrative(text))
