"""Colostle routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, RosterCreate
from api.services import colostle_service as cs
from api.services.session_service import app_session_payload, get_active_play_context
from src.config import GAME_COLOSTLE
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/colostle", tags=["colostle"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Colostle context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return cs.character_header(_ctx(app))


@router.get("/character")
def get_character(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {
        "entity": ctx.entity,
        "options": cs.character_options_payload(),
        "settings": ctx.settings,
    }


@router.put("/character")
def update_character(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = cs.persist_character(ctx, body.entity)
    return {"entity": entity, "header": cs.character_header(ctx)}


@router.post("/character/reset")
def reset_character(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = cs.reset_character(ctx)
    return {"entity": entity, "header": cs.character_header(ctx)}


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    store = get_play_store(GAME_COLOSTLE)
    active = store.roster.get_active_slot_id() if store else ""
    return {"entries": cs.roster_payload(), "active_id": active or ""}


@router.post("/roster")
def create_roster(body: RosterCreate, app: AppSession = Depends(get_app_session)):
    entity = cs.create_character_entry(body.name)
    entries = cs.roster_payload()
    return {"entity": entity, "entries": entries}


@router.post("/roster/{char_id}/switch")
def switch_roster(char_id: str, response: Response, app: AppSession = Depends(get_app_session)):
    ctx = cs.switch_character(app, char_id)
    store = get_play_store(GAME_COLOSTLE)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return app_session_payload(app)


@router.delete("/roster/{char_id}")
def delete_roster(char_id: str, app: AppSession = Depends(get_app_session)):
    cs.delete_character_entry(char_id)
    entries = cs.roster_payload()
    return {"entries": entries, "session": app_session_payload(app)}


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": cs.shortcuts_payload()}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        user_message, answer, sources, route = cs.execute_shortcut(ctx, shortcut_id, app=app)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = cs.append_chat_exchange(app, ctx, user_message, answer)
    app.last_sources = sources
    store = get_play_store(GAME_COLOSTLE)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "entity": ctx.entity,
        "header": cs.character_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_COLOSTLE)
    path = str(store.log_path(ctx.slot_id)) if store and ctx.slot_id else None
    return {"lines": cs.lonelog_tail(ctx, n_lines), "path": path}
