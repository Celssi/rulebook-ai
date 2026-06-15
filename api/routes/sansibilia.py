"""San Sibilia routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, RosterCreate, VisitAdvanceRequest, VisitCityChangeRequest
from api.services import sansibilia_service as ss
from api.services.session_service import app_session_payload, get_active_play_context
from src.config import GAME_SANSIBILIA
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/sansibilia", tags=["sansibilia"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "San Sibilia context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return ss.visit_header(_ctx(app))


@router.get("/visit")
def get_visit(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {
        "entity": ctx.entity,
        "options": ss.visit_options_payload(),
        "settings": ctx.settings,
    }


@router.put("/visit")
def update_visit(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = ss.persist_visit(ctx, body.entity)
    return {"entity": entity, "header": ss.visit_header(ctx)}


@router.post("/visit/reset")
def reset_visit(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = ss.reset_visit(ctx)
    return {"entity": entity, "header": ss.visit_header(ctx)}


@router.post("/visit/draw-character")
def draw_character(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        result = ss.draw_character_table(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": ss.visit_header(ctx), **result}


@router.post("/visit/draw-day")
def draw_day(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    try:
        day, user_message, answer = ss.perform_day_draw(ctx, chat_provider=app.chat_provider)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = ss.append_chat_exchange(app, ctx, user_message, answer)
    store = get_play_store(GAME_SANSIBILIA)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "entity": ctx.entity,
        "header": ss.visit_header(ctx),
        "messages": messages,
        "answer": answer,
        **day,
    }


@router.post("/visit/city-change")
def city_change(
    body: VisitCityChangeRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = ss.record_city_change(ctx, body.note)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": ss.visit_header(ctx), **result}


@router.post("/visit/advance-day")
def advance_day(
    body: VisitAdvanceRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    result = ss.advance_day(ctx, body.days_between)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": ss.visit_header(ctx), **result}


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    return {"entries": ss.roster_payload(), "active_id": _ctx(app).slot_id}


@router.post("/roster")
def create_roster_entry(body: RosterCreate, app: AppSession = Depends(get_app_session)):
    entity = ss.create_visit_entry(body.name)
    char_id = entity.get("id", "")
    ctx = ss.switch_visit(app, char_id)
    return {"entity": ctx.entity, "entries": ss.roster_payload()}


@router.post("/roster/{visit_id}/switch")
def switch_roster(visit_id: str, app: AppSession = Depends(get_app_session)):
    ss.switch_visit(app, visit_id)
    return app_session_payload(app)


@router.delete("/roster/{visit_id}")
def delete_roster(visit_id: str, app: AppSession = Depends(get_app_session)):
    ss.delete_visit_entry(visit_id)
    store = get_play_store(GAME_SANSIBILIA)
    if store:
        ctx = store.init_ctx()
        app.play[GAME_SANSIBILIA] = ctx
    return {"entries": ss.roster_payload(), "session": app_session_payload(app)}


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": ss.shortcuts_payload(_ctx(app))}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        user_message, answer, sources, route = ss.execute_shortcut(ctx, shortcut_id, app=app)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = ss.append_chat_exchange(app, ctx, user_message, answer)
    app.last_sources = sources
    store = get_play_store(GAME_SANSIBILIA)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "entity": ctx.entity,
        "header": ss.visit_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_SANSIBILIA)
    path = None
    if store and ctx.slot_id:
        try:
            path = str(store.log_path(ctx.slot_id))
        except RuntimeError:
            path = None
    return {"lines": ss.lonelog_tail(ctx, n_lines), "path": path}
