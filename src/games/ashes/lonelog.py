"""Ashes lonelog formatters."""

from __future__ import annotations

from src.games.ashes.play import get_ashes_store
from src.games.ashes.scion import AshesScion
from src.games.saves.lonelog import format_draw, format_narrative, format_player_action, format_scene


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    store = get_ashes_store()
    return store.read_log_tail(slot_id, n_lines)


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
        elif ln.startswith("d:"):
            snippets.append(ln)
    if not snippets:
        return ""
    tail = snippets[-max_entries:]
    body = "\n\n".join(tail)
    if len(body) > max_chars:
        body = body[-max_chars:].lstrip()
    return "Story so far in this run:\n\n" + body


def log_player_action(slot_id: str, text: str) -> None:
    get_ashes_store().append_log(slot_id, format_player_action(text))


def log_room(slot_id: str, scion: AshesScion, card: str, room: str, check: str) -> None:
    label = f"Room {scion.rooms_cleared + 1} {room} ({check})"
    get_ashes_store().append_log(slot_id, format_draw([card], label=label))


def log_journal(slot_id: str, card: str, event: str) -> None:
    get_ashes_store().append_log(slot_id, format_draw([card], label=event[:80]))


def log_roll(slot_id: str, label: str, detail: str) -> None:
    get_ashes_store().append_log(slot_id, format_draw([], label=f"{label}: {detail}"))


def log_narrative(slot_id: str, text: str) -> None:
    get_ashes_store().append_log(slot_id, format_narrative(text))


def open_run(slot_id: str, scion: AshesScion) -> None:
    store = get_ashes_store()
    store.append_log(slot_id, "")
    store.append_log(slot_id, format_scene(scion.rooms_cleared + 1, f"Mayfalls — {scion.name or 'Scion'}"))
