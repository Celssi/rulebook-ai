"""Apothecaria lonelog formatters."""

from __future__ import annotations

from src.games.apothecaria.play import get_apothecaria_store


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    store = get_apothecaria_store()
    return store.read_log_tail(slot_id, n_lines)


def log_draw(slot_id: str, label: str, card: str, detail: str = "") -> None:
    store = get_apothecaria_store()
    line = f"d: {label} — {card}"
    if detail:
        line += f" -> {detail[:120]}"
    store.append_log(slot_id, line)


def log_player_action(slot_id: str, text: str) -> None:
    store = get_apothecaria_store()
    store.append_log(slot_id, text if text.startswith("@") else f"@ {text}")


def log_narrative(slot_id: str, text: str) -> None:
    store = get_apothecaria_store()
    store.append_log(slot_id, f"=> {text[:200]}")


def narrative_context_for_ai(
    slot_id: str,
    *,
    max_entries: int = 8,
    max_chars: int = 3500,
) -> str:
    """Compact story thread from Lonelog => lines for AI narrator."""
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
    tail = snippets[-max_entries:]
    body = "\n\n".join(tail)
    if len(body) > max_chars:
        body = body[-max_chars:].lstrip()
        cut = body.find("\n\n")
        if 0 <= cut < 200:
            body = body[cut + 2 :]
    return (
        "Story so far in this cottage (chronological; continue naturally — do not repeat events):\n\n"
        + body
    )
