"""Session routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from api.deps import SESSION_COOKIE, get_app_session
from api.models import SessionUpdate
from api.services.session_service import app_session_payload, get_active_play_context
from api.utils import RETRIEVAL_PROFILES
from src.config import get_all_factions
from src.games.registry import get_game_plugin
from src.games.saves import AppSession, get_play_store
from src.llm import active_model_name, available_chat_providers, provider_display_name, resolve_anthropic_api_key
from src.config import EMBED_MODEL

router = APIRouter(prefix="/api/session", tags=["session"])


@router.get("")
def get_session(app: AppSession = Depends(get_app_session)):
    return app_session_payload(app)


@router.put("")
def update_session(
    body: SessionUpdate,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    if body.selected_game_id and body.selected_game_id != app.selected_game_id:
        store = get_play_store(app.selected_game_id)
        if store:
            ctx = get_active_play_context(app)
            if ctx:
                store.persist_ctx(ctx)
        app.selected_game_id = body.selected_game_id
        app.last_sources = []
        from api.services.session_service import _ensure_game_context

        _ensure_game_context(app)
    if body.chat_provider is not None:
        app.chat_provider = body.chat_provider  # type: ignore[assignment]
    if body.mode is not None:
        app.mode = body.mode
    if body.top_k is not None:
        app.top_k = body.top_k
    if body.retrieval_profile is not None:
        app.retrieval_profile = body.retrieval_profile
    if body.selected_factions is not None:
        app.selected_factions = body.selected_factions
    ctx = get_active_play_context(app)
    if ctx and body.settings:
        ctx.settings.update(body.settings)
        store = get_play_store(app.selected_game_id)
        if store:
            store.persist_ctx(ctx)
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return app_session_payload(app)


@router.get("/settings-meta")
def settings_meta(app: AppSession = Depends(get_app_session)):
    key = resolve_anthropic_api_key()
    providers = available_chat_providers(anthropic_key=key)
    plugin = get_game_plugin(app.selected_game_id)
    return {
        "chat_providers": [
            {"id": p, "label": provider_display_name(p), "model": active_model_name(p)}
            for p in providers
        ],
        "embed_model": EMBED_MODEL,
        "retrieval_profiles": list(RETRIEVAL_PROFILES.keys()),
        "factions": get_all_factions(app.selected_game_id),
        "ingest_all_label": plugin.ingest_all_label() if plugin else "",
        "ocr_available": bool(get_game_plugin(app.selected_game_id)),
    }
