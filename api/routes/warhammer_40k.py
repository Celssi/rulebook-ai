"""Warhammer 40k routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_app_session
from api.models import GameStateUpdate
from src.games.saves import AppSession
from src.games.warhammer_40k.state import format_summary, game_state_from_dict, game_state_to_dict

router = APIRouter(prefix="/api/warhammer40k", tags=["warhammer40k"])

ARMY_OPTIONS = {
    "": "—",
    "space_marines": "Space Marines",
    "tyranids": "Tyranids",
}

PHASE_OPTIONS = {
    "": "—",
    "command": "Command",
    "movement": "Movement",
    "shooting": "Shooting",
    "charge": "Charge",
    "fight": "Fight",
}

ACTIVE_OPTIONS = {
    "": "—",
    "me": "Me",
    "opponent": "Opponent",
}


@router.get("/state")
def get_state(app: AppSession = Depends(get_app_session)):
    gs = game_state_from_dict(app.game_state_40k)
    return {
        "game_state": app.game_state_40k,
        "summary": format_summary(gs, "en"),
        "options": {
            "armies": ARMY_OPTIONS,
            "phases": PHASE_OPTIONS,
            "active": ACTIVE_OPTIONS,
        },
    }


@router.put("/state")
def update_state(body: GameStateUpdate, app: AppSession = Depends(get_app_session)):
    app.game_state_40k = body.game_state
    gs = game_state_from_dict(app.game_state_40k)
    return {
        "game_state": app.game_state_40k,
        "summary": format_summary(gs, "en"),
    }
