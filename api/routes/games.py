"""Game listing routes."""

from __future__ import annotations

from fastapi import APIRouter

from src.games.registry import game_options

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
def list_games():
    return {"games": [{"id": gid, "label": label} for gid, label in game_options().items()]}
