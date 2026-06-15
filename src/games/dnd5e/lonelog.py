"""D&D 5e lonelog formatting."""

from __future__ import annotations

from src.games.saves import get_play_store
from src.games.saves.lonelog import format_mechanical, format_narrative

GAME_ID = "dnd5e"


def _store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("D&D 5e play profile not registered")
    return store


def read_tail(slot_id: str, n_lines: int = 50) -> list[str]:
    return _store().read_log_tail(slot_id, n_lines)


def narrative_context_for_ai(
    slot_id: str,
    *,
    campaign_setting: str = "freeform",
    campaign_notes: str = "",
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
    setting = (campaign_setting or "freeform").strip().lower()
    notes = (campaign_notes or "").strip()
    if setting == "faerun":
        prefix = "Story so far in Faerûn (continue naturally):"
    elif notes:
        prefix = f"Story so far in this campaign (continue naturally):\nSetting: {notes}"
    else:
        prefix = "Story so far (continue naturally):"
    return f"{prefix}\n\n{body}"


def log_roll(slot_id: str, label: str, summary: str) -> None:
    _store().append_log(slot_id, format_mechanical(f"{label}: {summary[:120]}"))


def log_narrative_line(slot_id: str, text: str) -> None:
    _store().append_log(slot_id, format_narrative(text))
