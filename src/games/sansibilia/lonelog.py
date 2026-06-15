"""San Sibilia Lonelog formatters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.sansibilia.play import get_sansibilia_store
from src.games.saves.lonelog import card_short_label, format_draw, format_mechanical, format_scene

if TYPE_CHECKING:
    from src.games.sansibilia.visit import SansibiliaVisit


def format_day_header(visit: SansibiliaVisit) -> str:
    return format_scene(visit.visit_day, f"San Sibilia, Day {visit.visit_day}")


def format_city_change_note(title: str, prompt: str) -> str:
    return format_mechanical(f"City change: {title} — {prompt}")


def format_day_draw_line(
    visit: SansibiliaVisit,
    card1: str,
    card2: str,
    adjective: str,
    location: str,
) -> str:
    label = f"Day {visit.visit_day} {adjective} · {location}"
    return format_draw(
        [card_short_label(card1), card_short_label(card2)],
        label=label,
    )


def format_day_draw(visit: SansibiliaVisit, card1: str, card2: str, adjective: str, location: str) -> str:
    return format_day_draw_line(visit, card1, card2, adjective, location)


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    store = get_sansibilia_store()
    return store.read_log_tail(slot_id, n_lines)


def narrative_context_for_ai(
    slot_id: str,
    *,
    max_entries: int = 8,
    max_chars: int = 3500,
) -> str:
    """Compact story thread from Lonelog => lines and scene headers for AI narrator."""
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
        elif ln.startswith("->") and "city change" in ln.lower():
            snippets.append(ln[2:].strip())
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
        "Story so far in this visit (chronological; continue naturally — do not repeat events):\n\n"
        + body
    )


def log_day_draw(
    slot_id: str,
    visit: SansibiliaVisit,
    card1: str,
    card2: str,
    adjective: str,
    location: str,
) -> None:
    store = get_sansibilia_store()
    store.append_log(slot_id, format_day_draw_line(visit, card1, card2, adjective, location))


def log_city_change(slot_id: str, title: str, prompt: str) -> None:
    store = get_sansibilia_store()
    store.append_log(slot_id, format_city_change_note(title, prompt))


def log_player_action(slot_id: str, text: str) -> None:
    from src.games.saves.lonelog import format_player_action

    store = get_sansibilia_store()
    store.append_log(slot_id, format_player_action(text))


def log_narrative(slot_id: str, text: str) -> None:
    from src.games.saves.lonelog import format_narrative

    store = get_sansibilia_store()
    store.append_log(slot_id, format_narrative(text))


def open_day(slot_id: str, visit: SansibiliaVisit) -> None:
    store = get_sansibilia_store()
    store.append_log(slot_id, "")
    store.append_log(slot_id, format_day_header(visit))
