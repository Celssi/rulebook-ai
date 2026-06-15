"""Factory for GM solo FastAPI routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import CharacterUpdate, RosterCreate
from api.services.session_service import app_session_payload, get_active_play_context
from src.games.saves import AppSession, get_play_store


def build_gm_router(
    game_id: str,
    service_module,
    *,
    tags: list[str] | None = None,
) -> APIRouter:
    router = APIRouter(prefix=f"/api/{game_id}", tags=tags or [game_id])

    def _ctx(app: AppSession):
        ctx = get_active_play_context(app)
        if not ctx or ctx.game_id != game_id:
            raise HTTPException(400, f"{game_id} context unavailable")
        return ctx

    @router.get("/header")
    def header(app: AppSession = Depends(get_app_session)):
        return service_module.character_header(_ctx(app))

    @router.get("/character")
    def get_character(app: AppSession = Depends(get_app_session)):
        ctx = _ctx(app)
        options = {}
        if hasattr(service_module, "character_options_payload"):
            options = service_module.character_options_payload()
        return {"entity": ctx.entity, "options": options, "settings": ctx.settings}

    @router.put("/character")
    def update_character(body: CharacterUpdate, app: AppSession = Depends(get_app_session)):
        ctx = _ctx(app)
        entity = service_module.persist_character(ctx, body.entity)
        return {"entity": entity, "header": service_module.character_header(ctx)}

    @router.post("/character/reset")
    def reset_character(app: AppSession = Depends(get_app_session)):
        ctx = _ctx(app)
        entity = service_module.reset_character(ctx)
        return {"entity": entity, "header": service_module.character_header(ctx)}

    @router.get("/roster")
    def roster(app: AppSession = Depends(get_app_session)):
        store = get_play_store(game_id)
        active = store.roster.get_active_slot_id() if store else ""
        return {"entries": service_module.roster_payload(), "active_id": active or ""}

    @router.post("/roster")
    def create_roster(body: RosterCreate, app: AppSession = Depends(get_app_session)):
        entity = service_module.create_character_entry(body.name)
        entries = service_module.roster_payload()
        return {"entity": entity, "entries": entries}

    @router.post("/roster/{char_id}/switch")
    def switch_roster(char_id: str, response: Response, app: AppSession = Depends(get_app_session)):
        ctx = service_module.switch_character(app, char_id)
        store = get_play_store(game_id)
        if store:
            store.persist_ctx(ctx)
        response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
        return app_session_payload(app)

    @router.delete("/roster/{char_id}")
    def delete_roster(char_id: str, app: AppSession = Depends(get_app_session)):
        service_module.delete_character_entry(char_id)
        entries = service_module.roster_payload()
        return {"entries": entries, "session": app_session_payload(app)}

    @router.get("/shortcuts")
    def shortcuts(app: AppSession = Depends(get_app_session)):
        ctx = _ctx(app)
        if hasattr(service_module, "shortcuts_payload"):
            return {"shortcuts": service_module.shortcuts_payload(ctx)}
        return {"shortcuts": service_module.shortcuts_payload()}

    @router.post("/shortcuts/{shortcut_id}")
    def run_shortcut_route(
        shortcut_id: str,
        response: Response,
        body: dict[str, Any] | None = Body(default=None),
        app: AppSession = Depends(get_app_session),
    ):
        ctx = _ctx(app)
        params = {k: v for k, v in (body or {}).items() if v is not None}
        try:
            user_message, answer, sources, route = service_module.execute_shortcut(
                ctx, shortcut_id, app=app, params=params or None
            )
        except ValueError as e:
            raise HTTPException(400, str(e)) from e
        messages = service_module.append_chat_exchange(app, ctx, user_message, answer)
        app.last_sources = sources
        store = get_play_store(game_id)
        if store:
            store.persist_ctx(ctx)
        response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
        return {
            "answer": answer,
            "sources": sources,
            "route": route,
            "messages": messages,
            "entity": ctx.entity,
            "header": service_module.character_header(ctx),
        }

    @router.get("/lonelog")
    def lonelog(app: AppSession = Depends(get_app_session), n_lines: int = 50):
        ctx = _ctx(app)
        store = get_play_store(game_id)
        path = str(store.log_path(ctx.slot_id)) if store and ctx.slot_id else None
        return {"lines": service_module.lonelog_tail(ctx, n_lines), "path": path}

    return router
