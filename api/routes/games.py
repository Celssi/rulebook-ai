"""Game listing routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.games.how_to_play import how_to_play_response
from src.games.registry import game_options

router = APIRouter(prefix="/api/games", tags=["games"])


@router.get("")
def list_games():
    return {"games": [{"id": gid, "label": label} for gid, label in game_options().items()]}


@router.get("/{game_id}/how-to-play")
def get_how_to_play(game_id: str):
    if game_id == "40k":
        raise HTTPException(status_code=404, detail="How-to-play guide not available for this game")
    payload = how_to_play_response(game_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="How-to-play guide not found")
    return payload
