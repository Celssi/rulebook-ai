"""Brambletrek 2 Lonelog formatters."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.brambletrek_2.play import get_brambletrek_2_store
from src.games.saves import lonelog as lonelog_fmt
from src.games.saves.lonelog import card_short_label, format_pc, format_scene

if TYPE_CHECKING:
    from src.games.brambletrek_2.character import Brambletrek2Character

format_draw = lonelog_fmt.format_draw
format_mechanical = lonelog_fmt.format_mechanical
format_narrative = lonelog_fmt.format_narrative
format_player_action = lonelog_fmt.format_player_action


def format_resources(
    health: int,
    morale: int,
    supplies: int,
    *,
    name: str = "",
) -> str:
    return format_pc(
        name.strip() or "Traveller",
        f"Health {health}",
        f"Morale {morale}",
        f"Supplies {supplies}",
    )


def format_scene_header(char: Brambletrek2Character, location_hint: str = "") -> str:
    loc = location_hint.strip()
    if not loc:
        loc = "Misty Hollow" if char.in_hollow else "Hundred Acre Woods"
    context = f"{loc}, day {char.exploration_day}"
    if char.in_hollow:
        context += f", fragments {char.memory_fragments}/3"
    return format_scene(char.exploration_day, context)


def format_resource_snapshot(char: Brambletrek2Character) -> str:
    return format_resources(
        char.health,
        char.morale,
        char.supplies,
        name=char.name.strip() or "Traveller",
    )


def open_scene(slot_id: str, char: Brambletrek2Character, location_hint: str = "", *, st=None) -> None:
    store = get_brambletrek_2_store()
    store.append_log(slot_id, "", st=st)
    store.append_log(slot_id, format_scene_header(char, location_hint), st=st)
    store.log_tag(slot_id, format_resource_snapshot(char), st=st)


def log_draw(slot_id: str, cards: list[str], *, label: str = "Drew", char=None, st=None) -> None:
    _ = char
    get_brambletrek_2_store().log_draw(slot_id, cards, label=label, st=st)


def log_mechanical(slot_id: str, text: str, *, char=None, st=None) -> None:
    _ = char
    get_brambletrek_2_store().log_mechanical(slot_id, text, st=st)


def log_narrative(slot_id: str, text: str, *, char=None, st=None) -> None:
    _ = char
    get_brambletrek_2_store().log_narrative(slot_id, text, st=st)


def log_player_action(slot_id: str, text: str, *, char=None, st=None) -> None:
    _ = char
    get_brambletrek_2_store().log_player_action(slot_id, text, st=st)


def log_oracle(slot_id: str, text: str, *, char=None, st=None) -> None:
    _ = char
    get_brambletrek_2_store().log_oracle_question(slot_id, text, st=st)


def read_tail(slot_id: str, n_lines: int = 30) -> list[str]:
    return get_brambletrek_2_store().read_log_tail(slot_id, n_lines=n_lines)
