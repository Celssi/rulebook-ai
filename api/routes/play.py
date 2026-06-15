"""Generic play-mode routes (roster games)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_app_session
from api.services.play_service import (
    header_payload,
    lonelog_path,
    lonelog_tail,
    roster_payload,
    shortcuts_payload,
)
from api.services.session_service import get_active_play_context
from src.games.saves import AppSession, has_play_roster

router = APIRouter(prefix="/api/play", tags=["play"])


def _ctx(app: AppSession, game_id: str):
    if not has_play_roster(game_id):
        raise HTTPException(404, f"Game {game_id!r} has no play roster")
    ctx = get_active_play_context(app)
    if not ctx or ctx.game_id != game_id:
        raise HTTPException(400, f"Active context for {game_id!r} unavailable")
    return ctx


@router.get("/{game_id}/header")
def header(game_id: str, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app, game_id)
    return header_payload(game_id, ctx)


@router.get("/{game_id}/roster")
def roster(game_id: str, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app, game_id)
    return {"entries": roster_payload(game_id), "active_id": ctx.slot_id}


@router.get("/{game_id}/shortcuts")
def shortcuts(game_id: str, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app, game_id)
    return {"shortcuts": shortcuts_payload(game_id, ctx)}


@router.get("/{game_id}/lonelog")
def lonelog(game_id: str, app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app, game_id)
    path = lonelog_path(game_id, ctx)
    return {"lines": lonelog_tail(game_id, ctx, n_lines), "path": path}
