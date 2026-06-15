"""Generic play-mode API helpers."""

from __future__ import annotations

import importlib
from typing import Any

from src.games.saves import PlayContext, get_play_profile, get_play_store, has_play_roster


def _handlers(game_id: str):
    if not has_play_roster(game_id):
        raise ValueError(f"Game {game_id!r} has no play roster")
    return importlib.import_module(f"src.games.{game_id}.play_handlers")


def require_play_context(game_id: str, ctx: PlayContext | None) -> PlayContext:
    if ctx is None or ctx.game_id != game_id:
        raise ValueError(f"Active play context for {game_id!r} unavailable")
    return ctx


def shortcuts_payload(game_id: str, ctx: PlayContext) -> list[dict]:
    handlers = _handlers(game_id)
    if hasattr(handlers, "shortcuts_payload"):
        return list(handlers.shortcuts_payload(ctx))
    return []


def lonelog_tail(game_id: str, ctx: PlayContext, n_lines: int = 50) -> list[str]:
    handlers = _handlers(game_id)
    if hasattr(handlers, "lonelog_tail"):
        return list(handlers.lonelog_tail(ctx, n_lines))
    store = get_play_store(game_id)
    if store and ctx.slot_id:
        return store.read_log_tail(ctx.slot_id, n_lines)
    return []


def lonelog_path(game_id: str, ctx: PlayContext) -> str | None:
    store = get_play_store(game_id)
    if not store or not ctx.slot_id or not store.lonelog:
        return None
    return str(store.log_path(ctx.slot_id))


def roster_payload(game_id: str) -> list[dict]:
    handlers = _handlers(game_id)
    if hasattr(handlers, "roster_payload"):
        return list(handlers.roster_payload())
    store = get_play_store(game_id)
    if not store:
        return []
    return [{"id": e.id, "name": e.name} for e in store.list_slots()]


def header_payload(game_id: str, ctx: PlayContext) -> dict[str, Any]:
    handlers = _handlers(game_id)
    for name in (
        "character_header",
        "visit_header",
        "watch_header",
        "cottage_header",
        "investigation_header",
        "scion_header",
    ):
        fn = getattr(handlers, name, None)
        if callable(fn):
            return dict(fn(ctx))
    profile = get_play_profile(game_id)
    if profile and ctx.entity is not None:
        entity = profile.entity_from_dict(ctx.entity)
        return {"name": profile.slot_display_name(entity)}
    return {}
