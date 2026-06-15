"""Apothecaria routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import ApothecariaBuyRequest, ApothecariaHuntRequest, ApothecariaLocaleRequest, ApothecariaShortcutParams, CharacterUpdate, RosterCreate
from api.services import apothecaria_service as apo
from api.services.session_service import app_session_payload, get_active_play_context
from src.config import GAME_APOTHECARIA
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/apothecaria", tags=["apothecaria"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Apothecaria context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return apo.cottage_header(_ctx(app))


@router.get("/cottage")
def get_cottage(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    return {
        "entity": ctx.entity,
        "options": apo.cottage_options_payload(),
        "settings": ctx.settings,
    }


@router.put("/cottage")
def update_cottage(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = apo.persist_cottage(ctx, body.entity)
    return {"entity": entity, "header": apo.cottage_header(ctx)}


@router.post("/cottage/reset")
def reset_cottage(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = apo.reset_cottage(ctx)
    return {"entity": entity, "header": apo.cottage_header(ctx)}


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    return {"entries": apo.roster_payload(), "active_id": _ctx(app).slot_id}


@router.post("/roster")
def create_roster_entry(body: RosterCreate, app: AppSession = Depends(get_app_session)):
    entity = apo.create_cottage_entry(body.name)
    char_id = entity.get("id", "")
    ctx = apo.switch_cottage(app, char_id)
    return {"entity": ctx.entity, "entries": apo.roster_payload()}


@router.post("/roster/{cottage_id}/switch")
def switch_roster(cottage_id: str, app: AppSession = Depends(get_app_session)):
    apo.switch_cottage(app, cottage_id)
    return app_session_payload(app)


@router.delete("/roster/{cottage_id}")
def delete_roster(cottage_id: str, app: AppSession = Depends(get_app_session)):
    apo.delete_cottage_entry(cottage_id)
    store = get_play_store(GAME_APOTHECARIA)
    if store:
        ctx = store.init_ctx()
        app.play[GAME_APOTHECARIA] = ctx
    return {"entries": apo.roster_payload(), "session": app_session_payload(app)}


@router.post("/cottage/change-locale")
def change_locale_route(
    body: ApothecariaLocaleRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = apo.change_locale_action(ctx, body.locale_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.post("/cottage/hunt")
def hunt_reagent_route(
    body: ApothecariaHuntRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = apo.hunt_reagent_action(ctx, body.reagent_name)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.post("/cottage/complete-potion")
def complete_potion_route(
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = apo.complete_potion_action(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.post("/cottage/advance-week")
def advance_week_route(
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    result = apo.advance_week_action(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.post("/cottage/advance-downtime")
def advance_downtime_route(
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = apo.advance_downtime_action(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.post("/cottage/buy-tool")
def buy_tool_route(
    body: ApothecariaBuyRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = apo.buy_tool_action(ctx, body.item_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.post("/cottage/buy-upgrade")
def buy_upgrade_route(
    body: ApothecariaBuyRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = apo.buy_upgrade_action(ctx, body.item_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {"entity": ctx.entity, "header": apo.cottage_header(ctx), **result}


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": apo.shortcuts_payload(_ctx(app))}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    body: ApothecariaShortcutParams | None = None,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    params = body.model_dump(exclude_none=True) if body else {}
    try:
        user_message, answer, sources, route = apo.execute_shortcut(
            ctx, shortcut_id, app=app, params=params or None
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    messages = apo.append_chat_exchange(app, ctx, user_message, answer)
    app.last_sources = sources
    store = get_play_store(GAME_APOTHECARIA)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "entity": ctx.entity,
        "header": apo.cottage_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_APOTHECARIA)
    path = None
    if store and ctx.slot_id:
        try:
            path = str(store.log_path(ctx.slot_id))
        except RuntimeError:
            path = None
    return {"lines": apo.lonelog_tail(ctx, n_lines), "path": path}
