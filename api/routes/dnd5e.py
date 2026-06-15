"""D&D 5e API routes."""

from __future__ import annotations

from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from api.deps import get_app_session
from api.services import dnd5e_service as service_module
from api.routes.gm_solo_factory import build_gm_router
from api.services.session_service import get_active_play_context
from src.games.saves import AppSession, get_play_store

router = build_gm_router("dnd5e", service_module, tags=["dnd5e"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx or ctx.game_id != "dnd5e":
        raise HTTPException(400, "dnd5e context unavailable")
    return ctx


class LevelUpBody(BaseModel):
    hp_roll: int | None = Field(default=None, ge=1, le=12)


@router.post("/character/level-up")
def level_up_route(body: LevelUpBody, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = service_module.level_up_character(ctx, hp_roll=body.hp_roll)
    store = get_play_store("dnd5e")
    if store:
        store.persist_ctx(ctx)
    return {
        "entity": entity,
        "header": service_module.character_header(ctx),
        "summary": service_module.creation_summary(ctx),
    }


@router.get("/character/summary")
def creation_summary_route(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return service_module.creation_summary(ctx)
