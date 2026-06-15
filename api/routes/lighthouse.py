"""Lighthouse routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, RosterCreate
from api.services import lighthouse_service as lh
from api.services.session_service import app_session_payload, get_active_play_context
from src.config import GAME_LIGHTHOUSE
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/lighthouse", tags=["lighthouse"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Lighthouse context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return lh.watch_header(_ctx(app))


@router.get("/watch")
def get_watch(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {
        "entity": ctx.entity,
        "options": lh.watch_options_payload(),
        "settings": ctx.settings,
    }


@router.put("/watch")
def update_watch(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = lh.persist_watch(ctx, body.entity)
    return {"entity": entity, "header": lh.watch_header(ctx)}


@router.post("/watch/reset")
def reset_watch(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = lh.reset_watch(ctx)
    return {"entity": entity, "header": lh.watch_header(ctx)}


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    store = get_play_store(GAME_LIGHTHOUSE)
    active = store.roster.get_active_slot_id() if store else ""
    return {"entries": lh.roster_payload(), "active_id": active or ""}


@router.post("/roster")
def create_roster(body: RosterCreate, app: AppSession = Depends(get_app_session)):
    entity = lh.create_watch_entry(body.name)
    entries = lh.roster_payload()
    return {"entity": entity, "entries": entries}


@router.post("/roster/{watch_id}/switch")
def switch_roster(watch_id: str, response: Response, app: AppSession = Depends(get_app_session)):
    ctx = lh.switch_watch(app, watch_id)
    store = get_play_store(GAME_LIGHTHOUSE)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return app_session_payload(app)


@router.delete("/roster/{watch_id}")
def delete_roster(watch_id: str, app: AppSession = Depends(get_app_session)):
    lh.delete_watch_entry(watch_id)
    entries = lh.roster_payload()
    return {"entries": entries, "session": app_session_payload(app)}


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": lh.shortcuts_payload()}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        user_message, answer, sources, route = lh.execute_shortcut(ctx, shortcut_id, app=app)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = lh.append_chat_exchange(app, ctx, user_message, answer)
    app.last_sources = sources
    store = get_play_store(GAME_LIGHTHOUSE)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "entity": ctx.entity,
        "header": lh.watch_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_LIGHTHOUSE)
    path = str(store.log_path(ctx.slot_id)) if store and ctx.slot_id else None
    return {"lines": lh.lonelog_tail(ctx, n_lines), "path": path}
