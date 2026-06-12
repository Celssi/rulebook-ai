"""Brambletrek-specific Lonelog formatters (scene headers, resources)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.brambletrek.play import get_brambletrek_store
from src.games.saves import lonelog as lonelog_fmt
from src.games.saves.lonelog import card_short_label, format_pc, format_scene

if TYPE_CHECKING:
    from src.games.brambletrek.character import BrambletrekCharacter

# Re-export generic formatters for convenience
format_draw = lonelog_fmt.format_draw
format_mechanical = lonelog_fmt.format_mechanical
format_narrative = lonelog_fmt.format_narrative
format_player_action = lonelog_fmt.format_player_action
format_roll = lonelog_fmt.format_roll
format_resolution = lonelog_fmt.format_resolution
format_oracle_question = lonelog_fmt.format_oracle_question
format_table = lonelog_fmt.format_table
format_tag = lonelog_fmt.format_tag
format_npc = lonelog_fmt.format_npc
format_location = lonelog_fmt.format_location
format_thread = lonelog_fmt.format_thread
format_clock = lonelog_fmt.format_clock
format_track = lonelog_fmt.format_track


def format_resources(
    health: int,
    morale: int,
    supplies: int,
    *,
    name: str = "",
) -> str:
    """[PC:Name|Health 10|Morale 8|Supplies 7] per Lonelog resource tracking."""
    return format_pc(
        name.strip() or "Gnawborn",
        f"Health {health}",
        f"Morale {morale}",
        f"Supplies {supplies}",
    )


def format_scene_header(char: BrambletrekCharacter, location_hint: str = "") -> str:
    loc = location_hint.strip()
    if not loc:
        if char.in_aldwund:
            loc = "Aldwund Depths"
        elif char.active_adventure:
            from src.games.brambletrek.curated import adventure_meta

            adv = adventure_meta(char.active_adventure)
            loc = adv.get("label", char.active_adventure)
        else:
            loc = "Hyhill surface"
    context = f"{loc}, day {char.journey_day}"
    return format_scene(char.journey_day, context)


def format_resource_snapshot(char: BrambletrekCharacter) -> str:
    return format_resources(
        char.health,
        char.morale,
        char.supplies,
        name=char.name.strip() or "Gnawborn",
    )


def open_scene(slot_id: str, char: BrambletrekCharacter, location_hint: str = "", *, st=None) -> None:
    store = get_brambletrek_store()
    store.append_log(slot_id, "", st=st)
    store.append_log(slot_id, format_scene_header(char, location_hint), st=st)
    store.log_tag(slot_id, format_resource_snapshot(char), st=st)


def log_draw(
    slot_id: str,
    cards: list[str],
    *,
    label: str = "Drew",
    char: BrambletrekCharacter | None = None,
    st=None,
) -> None:
    _ = char
    get_brambletrek_store().log_draw(slot_id, cards, label=label, st=st)


def log_mechanical(
    slot_id: str,
    text: str,
    *,
    char: BrambletrekCharacter | None = None,
    st=None,
) -> None:
    _ = char
    get_brambletrek_store().log_mechanical(slot_id, text, st=st)


def log_narrative(
    slot_id: str,
    text: str,
    *,
    char: BrambletrekCharacter | None = None,
    st=None,
) -> None:
    _ = char
    get_brambletrek_store().log_narrative(slot_id, text, st=st)


def log_player_action(
    slot_id: str,
    text: str,
    *,
    char: BrambletrekCharacter | None = None,
    st=None,
) -> None:
    _ = char
    get_brambletrek_store().log_player_action(slot_id, text, st=st)


def log_oracle(
    slot_id: str,
    text: str,
    *,
    char: BrambletrekCharacter | None = None,
    st=None,
) -> None:
    _ = char
    get_brambletrek_store().log_oracle_question(slot_id, text, st=st)


def append_entry(
    slot_id: str,
    line: str,
    *,
    char: BrambletrekCharacter | None = None,
    st=None,
) -> None:
    _ = char
    get_brambletrek_store().append_log(slot_id, line, st=st)


def recent_context(slot_id: str, n_lines: int = 40) -> str:
    return get_brambletrek_store().recent_log_context(slot_id, n_lines=n_lines)


def read_tail(slot_id: str, n_lines: int = 30) -> list[str]:
    return get_brambletrek_store().read_log_tail(slot_id, n_lines=n_lines)


def log_path(slot_id: str):
    return get_brambletrek_store().log_path(slot_id)
