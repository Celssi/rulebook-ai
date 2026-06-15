"""Ashes routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, RosterCreate
from api.services import ashes_service as ash
from api.services.session_service import app_session_payload, get_active_play_context
from src.config import GAME_ASHES
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/ashes", tags=["ashes"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Ashes context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return ash.scion_header(_ctx(app))


@router.get("/scion")
def get_scion(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {
        "entity": ctx.entity,
        "options": ash.scion_options_payload(),
        "settings": ctx.settings,
    }


@router.put("/scion")
def update_scion(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = ash.persist_scion(ctx, body.entity)
    return {"entity": entity, "header": ash.scion_header(ctx)}


@router.post("/scion/reset")
def reset_scion(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = ash.reset_scion(ctx)
    return {"entity": entity, "header": ash.scion_header(ctx)}


@router.post("/scion/draw-gift")
def draw_gift(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        result = ash.draw_character_gift(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": ash.scion_header(ctx), **result}


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    store = get_play_store(GAME_ASHES)
    active = store.roster.get_active_slot_id() if store else ""
    return {"entries": ash.roster_payload(), "active_id": active or ""}


@router.post("/roster")
def create_roster_entry(body: RosterCreate, response: Response, app: AppSession = Depends(get_app_session)):
    entity = ash.create_scion_entry(body.name)
    store = get_play_store(GAME_ASHES)
    if store:
        ctx = app.play_context(GAME_ASHES)
        slot_id = str(entity.get("id") or "")
        if slot_id:
            ctx = store.switch_slot_ctx(ctx, slot_id)
            app.play[GAME_ASHES] = ctx
            store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "entity": entity,
        "entries": ash.roster_payload(),
        "session": app_session_payload(app),
    }


@router.post("/roster/{scion_id}/switch")
def switch_roster(scion_id: str, response: Response, app: AppSession = Depends(get_app_session)):
    ash.switch_scion(app, scion_id)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return app_session_payload(app)


@router.delete("/roster/{scion_id}")
def delete_roster(scion_id: str, app: AppSession = Depends(get_app_session)):
    ash.delete_scion_entry(scion_id)
    store = get_play_store(GAME_ASHES)
    entries = ash.roster_payload()
    if store and store.roster.get_active_slot_id() == scion_id:
        if entries:
            ash.switch_scion(app, entries[0]["id"])
    return {"entries": entries, "session": app_session_payload(app)}


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": ash.shortcuts_payload(_ctx(app))}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut(
    shortcut_id: str,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        user_message, answer, sources, route = ash.execute_shortcut(ctx, shortcut_id, app=app)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = ash.append_chat_exchange(app, ctx, user_message, answer)
    store = get_play_store(GAME_ASHES)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "entity": ctx.entity,
        "header": ash.scion_header(ctx),
        "messages": messages,
        "answer": answer,
        "sources": sources,
        "route": route,
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {"lines": ash.lonelog_tail(ctx)}
