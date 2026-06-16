"""Brambletrek routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterTableDrawRequest, CharacterUpdate, JourneyApplyRequest, ResourceBonusRequest, RosterCreate
from api.services import brambletrek_service as bt
from api.services.session_service import app_session_payload, get_active_play_context, get_messages
from src.config import GAME_BRAMBLETREK
from src.games.saves import AppSession, get_play_store

router = APIRouter(prefix="/api/brambletrek", tags=["brambletrek"])


def _ctx(app: AppSession):
    ctx = get_active_play_context(app)
    if not ctx:
        raise HTTPException(400, "Brambletrek context unavailable")
    return ctx


@router.get("/header")
def header(app: AppSession = Depends(get_app_session)):
    return bt.character_header(_ctx(app))


@router.get("/character")
def get_character(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    char = bt.get_character(ctx)
    used = dict(char.legacy_abilities_used or {})
    return {
        "entity": ctx.entity,
        "abilities": bt.legacy_abilities_payload(char.legacy, used) if char.legacy else [],
        "options": bt.character_options_payload(),
        "settings": ctx.settings,
        "resource_draft": bt.resource_draft_response(ctx, ctx.extra.get("resource_draft")),
    }


@router.put("/character")
def update_character(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = bt.persist_character(ctx, body.entity)
    return {"entity": entity, "header": bt.character_header(ctx)}


@router.post("/character/draw-table")
def draw_character_table(
    body: CharacterTableDrawRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.draw_character_table(ctx, body.table)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/character/draw-resources")
def draw_character_resources(
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.draw_character_resources(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/character/resource-bonus")
def draw_character_resource_bonus(
    body: ResourceBonusRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.draw_character_resource_bonus(ctx, body.stat)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/character/apply-resources")
def apply_character_resources(
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.apply_character_resources(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/character/roll-legacy")
def roll_character_legacy(
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.roll_character_legacy(ctx)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/character/reset")
def reset_character(app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    entity = bt.reset_character(ctx)
    return {"entity": entity, "header": bt.character_header(ctx)}


@router.get("/roster")
def roster(app: AppSession = Depends(get_app_session)):
    return {"entries": bt.roster_payload(), "active_id": _ctx(app).slot_id}


@router.post("/roster")
def create_roster_entry(body: RosterCreate, app: AppSession = Depends(get_app_session)):
    entity = bt.create_gnawborn(body.name)
    char_id = entity.get("id", "")
    ctx = bt.switch_gnawborn(app, char_id)
    return {"entity": ctx.entity, "entries": bt.roster_payload()}


@router.post("/roster/{char_id}/switch")
def switch_roster(char_id: str, app: AppSession = Depends(get_app_session)):
    ctx = bt.switch_gnawborn(app, char_id)
    return app_session_payload(app)


@router.delete("/roster/{char_id}")
def delete_roster(char_id: str, app: AppSession = Depends(get_app_session)):
    bt.delete_gnawborn(char_id)
    store = get_play_store(GAME_BRAMBLETREK)
    if store:
        ctx = store.init_ctx()
        app.play[GAME_BRAMBLETREK] = ctx
    return {"entries": bt.roster_payload(), "session": app_session_payload(app)}


@router.get("/journey")
def get_journey(app: AppSession = Depends(get_app_session)):
    return {"pending_journey": bt.pending_journey_payload(_ctx(app))}


@router.post("/journey/apply")
def apply_journey(
    body: JourneyApplyRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.apply_journey_event(ctx, body.event_index)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/journey/draw-item")
def draw_journey_item(
    body: JourneyApplyRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    try:
        result = bt.draw_journey_item(ctx, body.event_index)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/journey/finish")
def finish_journey(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    result = bt.finish_journey_day(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/journey/discard")
def discard_journey(response: Response, app: AppSession = Depends(get_app_session)):
    ctx = _ctx(app)
    result = bt.discard_journey(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return result


@router.post("/journey/bulk-apply")
def bulk_apply_journey(app: AppSession = Depends(get_app_session)):
    return bt.bulk_apply_journey(_ctx(app))


@router.get("/shortcuts")
def shortcuts(app: AppSession = Depends(get_app_session)):
    return {"shortcuts": bt.shortcuts_payload(_ctx(app))}


@router.post("/shortcuts/{shortcut_id}")
def run_shortcut_route(
    shortcut_id: str,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    ctx = _ctx(app)
    user_message, answer, sources, route = bt.execute_shortcut(ctx, shortcut_id, app=app)
    messages = list(get_messages(app))
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": answer})
    from api.services.session_service import sync_messages_to_context

    sync_messages_to_context(app, messages)
    app.last_sources = sources
    store = get_play_store(GAME_BRAMBLETREK)
    if store:
        store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return {
        "answer": answer,
        "sources": sources,
        "route": route,
        "messages": messages,
        "pending_journey": bt.pending_journey_payload(ctx),
        "entity": ctx.entity,
        "header": bt.character_header(ctx),
    }


@router.get("/lonelog")
def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
    ctx = _ctx(app)
    store = get_play_store(GAME_BRAMBLETREK)
    path = None
    if store and ctx.slot_id:
        try:
            path = str(store.log_path(ctx.slot_id))
        except RuntimeError:
            path = None
    return {"lines": bt.lonelog_tail(ctx, n_lines), "path": path}


@router.get("/reason-ending")
def reason_ending(reason_band: str, app: AppSession = Depends(get_app_session)):
    return {"preview": bt.reason_ending_preview(reason_band)}
