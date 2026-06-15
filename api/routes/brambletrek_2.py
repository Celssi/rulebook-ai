"""Brambletrek 2 routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, ExplorationApplyRequest, HollowMoveRequest, RosterCreate
from api.services import brambletrek_2_service as bt2
from api.services.session_service import app_session_payload, get_active_play_context, get_messages
from src.config import GAME_BRAMBLETREK_2
from src.games.saves import get_play_store

router = APIRouter(prefix="/api/brambletrek_2", tags=["brambletrek_2"])


def _ctx(app):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Brambletrek 2 context unavailable")
    return ctx


@router.get("/header")
def header(app=Depends(get_app_session)):
    return bt2.character_header(_ctx(app))


@router.get("/character")
def get_character(app=Depends(get_app_session)):
    ctx = _ctx(app)
    char = bt2.get_character(ctx)
    used = dict(char.legacy_abilities_used or {})
    return {
        "entity": ctx.entity,
        "abilities": bt2.legacy_abilities_payload(char.legacy, used) if char.legacy else [],
        "options": bt2.character_options_payload(),
        "settings": ctx.settings,
    }


@router.put("/character")
def update_character(body: CharacterUpdate, app=Depends(get_app_session)):
    ctx = _ctx(app)
    entity = bt2.persist_character(ctx, body.entity)
    return {"entity": entity, "header": bt2.character_header(ctx)}


@router.post("/character/draw-arrival")
def draw_arrival(response: Response, app=Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        result = bt2.draw_arrival(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/character/reset")
def reset_character(app=Depends(get_app_session)):
    ctx = _ctx(app)
    entity = bt2.reset_character(ctx)
    return {"entity": entity, "header": bt2.character_header(ctx)}


@router.get("/roster")
def roster(app=Depends(get_app_session)):
    return {"entries": bt2.roster_payload(), "active_id": _ctx(app).slot_id}


@router.post("/roster")
def create_roster_entry(body: RosterCreate, app=Depends(get_app_session)):
    entity = bt2.create_traveller(body.name)
    char_id = entity.get("id", "")
    ctx = bt2.switch_traveller(app, char_id)
    return {"entity": ctx.entity, "entries": bt2.roster_payload()}


@router.post("/roster/{char_id}/switch")
def switch_roster(char_id: str, app=Depends(get_app_session)):
    bt2.switch_traveller(app, char_id)
    return app_session_payload(app)


@router.delete("/roster/{char_id}")
def delete_roster(char_id: str, app=Depends(get_app_session)):
    bt2.delete_traveller(char_id)
    store = get_play_store(GAME_BRAMBLETREK_2)
    if store:
        ctx = store.init_ctx()
        app.play[GAME_BRAMBLETREK_2] = ctx
    return {"entries": bt2.roster_payload(), "session": app_session_payload(app)}


@router.get("/exploration")
def get_exploration(app=Depends(get_app_session)):
    return {"pending_exploration": bt2.pending_exploration_payload(_ctx(app))}


@router.post("/exploration/apply")
def apply_exploration(
    body: ExplorationApplyRequest,
    response: Response,
    app=Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt2.apply_exploration_event(ctx, body.event_index)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/exploration/finish")
def finish_exploration(response: Response, app=Depends(get_app_session)):
    ctx = _ctx(app)
    result = bt2.finish_exploration_day(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/exploration/discard")
def discard_exploration(response: Response, app=Depends(get_app_session)):
    ctx = _ctx(app)
    result = bt2.discard_exploration(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.get("/hollow")
def get_hollow(app=Depends(get_app_session)):
    return {"hollow": bt2.hollow_payload(_ctx(app))}


@router.post("/hollow/move")
def hollow_move(body: HollowMoveRequest, response: Response, app=Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        result = bt2.hollow_move(ctx, body.row, body.col)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.get("/shortcuts")
def shortcuts(app=Depends(get_app_session)):
    return {"shortcuts": bt2.shortcuts_payload(_ctx(app))}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    app=Depends(get_app_session),
):
    ctx = _ctx(app)
    user_message, answer, sources, route = bt2.execute_shortcut(ctx, shortcut_id, app=app)
    messages = list(get_messages(app))
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": answer})
    from api.services.session_service import sync_messages_to_context

    sync_messages_to_context(app, messages)
    app.last_sources = sources
    store = get_play_store(GAME_BRAMBLETREK_2)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "pending_exploration": bt2.pending_exploration_payload(ctx),
        "hollow": bt2.hollow_payload(ctx),
        "entity": ctx.entity,
        "header": bt2.character_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app=Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_BRAMBLETREK_2)
    path = None
    if store and ctx.slot_id:
        try:
            path = str(store.log_path(ctx.slot_id))
        except RuntimeError:
            path = None
    return {"lines": bt2.lonelog_tail(ctx, n_lines), "path": path}
