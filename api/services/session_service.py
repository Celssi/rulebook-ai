"""Session lifecycle for API requests."""

from __future__ import annotations

from src.config import DEFAULT_GAME_ID, get_all_factions
from src.games.registry import get_game_plugin
from src.games.saves import AppSession, PlayContext, SessionManager, get_play_store, has_play_roster
from src.games.warhammer_40k.state import default_state, game_state_to_dict

session_manager = SessionManager()


def ensure_app_session(session_id: str | None) -> AppSession:
    app = session_manager.get_or_create(session_id)
    _ensure_game_context(app)
    return app


def _ensure_game_context(app: AppSession) -> None:
    plugin = get_game_plugin(app.selected_game_id)
    if has_play_roster(app.selected_game_id):
        store = get_play_store(app.selected_game_id)
        if store and app.selected_game_id not in app.play:
            ctx = store.init_ctx()
            app.play[app.selected_game_id] = ctx
            app.play[app.selected_game_id].messages = ctx.messages
    if app.selected_game_id == "40k" and not app.game_state_40k:
        app.game_state_40k = game_state_to_dict(default_state())


def get_active_play_context(app: AppSession) -> PlayContext | None:
    store = get_play_store(app.selected_game_id)
    if not store:
        return None
    ctx = app.play_context(app.selected_game_id)
    if not ctx.slot_id:
        ctx = store.init_ctx()
        app.play[app.selected_game_id] = ctx
    return ctx


def sync_messages_to_context(app: AppSession, messages: list[dict[str, str]]) -> None:
    ctx = get_active_play_context(app)
    if ctx:
        ctx.messages = list(messages)
    else:
        app.messages = list(messages)


def get_messages(app: AppSession) -> list[dict[str, str]]:
    ctx = get_active_play_context(app)
    if ctx:
        return ctx.messages
    return app.messages


def default_factions(app: AppSession) -> list[str]:
    if app.selected_factions is not None:
        return app.selected_factions
    return get_all_factions(app.selected_game_id)


def app_session_payload(app: AppSession) -> dict:
    ctx = get_active_play_context(app)
    plugin = get_game_plugin(app.selected_game_id)
    payload: dict = {
        "session_id": app.session_id,
        "selected_game_id": app.selected_game_id,
        "chat_provider": app.chat_provider,
        "mode": app.mode,
        "top_k": app.top_k,
        "retrieval_profile": app.retrieval_profile,
        "selected_factions": default_factions(app),
        "last_sources": app.last_sources,
        "has_character_sheet": bool(plugin and plugin.has_character_sheet),
        "has_game_state": bool(plugin and plugin.has_game_state),
        "has_play_roster": has_play_roster(app.selected_game_id),
    }
    if ctx:
        payload["slot_id"] = ctx.slot_id
        payload["settings"] = ctx.settings
        payload["messages"] = ctx.messages
        payload["entity"] = ctx.entity
        payload["pending_journey"] = ctx.get_extra("pending_journey")
        payload["deck_remaining"] = len(ctx.deck or [])
    else:
        payload["messages"] = app.messages
    if app.selected_game_id == "40k":
        payload["game_state"] = app.game_state_40k
    return payload
