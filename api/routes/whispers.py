"""Whispers in the Walls routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, RosterCreate
from api.services import whispers_service as ws
from api.services.session_service import app_session_payload, get_active_play_context
from src.config import GAME_WHISPERS
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/whispers", tags=["whispers"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Whispers context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return ws.investigation_header(_ctx(app))


@router.get("/investigation")
def get_investigation(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {
        "entity": ctx.entity,
        "settings": ctx.settings,
    }


@router.put("/investigation")
def update_investigation(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = ws.persist_investigation(ctx, body.entity)
    return {"entity": entity, "header": ws.investigation_header(ctx)}


@router.post("/investigation/reset")
def reset_investigation(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = ws.reset_investigation(ctx)
    return {"entity": entity, "header": ws.investigation_header(ctx)}


@router.post("/investigation/build-deck")
def build_deck(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        draw = ws.build_deck(ctx)
        inv = ws.get_investigation(ctx)
        user_message = (
            f"**Whispers deck built** ({inv.cards_remaining() + 1} cards)\n\n"
            f"**Location draw:** {draw['location_card']}\n\n{draw.get('prompt', '')}"
        )
        answer = ws.build_draw_answer(ctx, inv, draw, chat_provider=app.chat_provider)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = ws.append_chat_exchange(app, ctx, user_message, answer)
    store = get_play_store(GAME_WHISPERS)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "entity": ctx.entity,
        "header": ws.investigation_header(ctx),
        "messages": messages,
        "answer": answer,
        **draw,
    }


@router.post("/investigation/draw")
def draw_whisper(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        draw, user_message, answer = ws.perform_whisper_draw(ctx, chat_provider=app.chat_provider)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = ws.append_chat_exchange(app, ctx, user_message, answer)
    store = get_play_store(GAME_WHISPERS)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "entity": ctx.entity,
        "header": ws.investigation_header(ctx),
        "messages": messages,
        "answer": answer,
        **draw,
    }


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    return {"entries": ws.roster_payload(), "active_id": _ctx(app).slot_id}


@router.post("/roster")
def create_roster_entry(body: RosterCreate, app: AppSession = Depends(get_app_session)):
    entity = ws.create_investigation_entry(body.name)
    char_id = entity.get("id", "")
    ctx = ws.switch_investigation(app, char_id)
    return {"entity": ctx.entity, "entries": ws.roster_payload()}


@router.post("/roster/{investigation_id}/switch")
def switch_roster(investigation_id: str, app: AppSession = Depends(get_app_session)):
    ws.switch_investigation(app, investigation_id)
    return app_session_payload(app)


@router.delete("/roster/{investigation_id}")
def delete_roster(investigation_id: str, app: AppSession = Depends(get_app_session)):
    ws.delete_investigation_entry(investigation_id)
    store = get_play_store(GAME_WHISPERS)
    if store:
        ctx = store.init_ctx()
        app.play[GAME_WHISPERS] = ctx
    return {"entries": ws.roster_payload(), "session": app_session_payload(app)}


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": ws.shortcuts_payload(_ctx(app))}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        user_message, answer, sources, route = ws.execute_shortcut(ctx, shortcut_id, app=app)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = ws.append_chat_exchange(app, ctx, user_message, answer)
    app.last_sources = sources
    store = get_play_store(GAME_WHISPERS)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "entity": ctx.entity,
        "header": ws.investigation_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_WHISPERS)
    path = None
    if store and ctx.slot_id:
        try:
            path = str(store.log_path(ctx.slot_id))
        except RuntimeError:
            path = None
    return {"lines": ws.lonelog_tail(ctx, n_lines), "path": path}
