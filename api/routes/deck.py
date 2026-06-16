"""Deck and dice routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_app_session
from api.models import DeckDrawRequest, DeckReportRequest, RollRequest
from api.services.session_service import get_active_play_context, get_messages, sync_messages_to_context
from src.games.saves import AppSession, get_play_store
from src.tools import (
    deck_remaining,
    deck_scope_key,
    draw_cards,
    format_card_result,
    format_dice_result,
    register_physical_card,
    reset_deck,
    roll_dice,
)

router = APIRouter(prefix="/api/deck", tags=["deck"])


def _deck_scope(app: AppSession, ctx) -> str:
    char_id = ctx.slot_id if ctx else None
    return deck_scope_key(app.selected_game_id, char_id)


@router.get("/status")
def deck_status(app: AppSession = Depends(get_app_session)):
    ctx = get_active_play_context(app)
    if ctx:
        ctx.sync_deck()
    remaining = deck_remaining(_deck_scope(app, ctx))
    card_source = "virtual"
    if ctx:
        from api.services.brambletrek_service import get_play_settings

        _, card_source = get_play_settings(ctx)
    return {"remaining": remaining, "card_source": card_source}


@router.post("/draw")
def draw(body: DeckDrawRequest, app: AppSession = Depends(get_app_session)):
    ctx = get_active_play_context(app)
    char_id = ctx.slot_id if ctx else None
    result = draw_cards(count=body.count, game_id=app.selected_game_id, char_id=char_id)
    if ctx:
        ctx.refresh_deck()
        store = get_play_store(app.selected_game_id)
        if char_id and result.get("ok") and result.get("cards") and store:
            store.log_draw(char_id, result["cards"], ctx=ctx)
            store.persist_ctx(ctx)
    return {
        "result": result,
        "formatted": format_card_result(result),
        "remaining": deck_remaining(_deck_scope(app, ctx)),
    }


@router.post("/report")
def report_physical(body: DeckReportRequest, app: AppSession = Depends(get_app_session)):
    ctx = get_active_play_context(app)
    char_id = ctx.slot_id if ctx else None
    result = register_physical_card(body.card, game_id=app.selected_game_id, char_id=char_id)
    if ctx:
        ctx.refresh_deck()
        store = get_play_store(app.selected_game_id)
        if char_id and result.get("ok") and result.get("cards") and store:
            store.log_draw(char_id, result["cards"], label="Physical draw", ctx=ctx)
            store.persist_ctx(ctx)
    return {"result": result, "formatted": format_card_result(result)}


@router.post("/reset")
def reset(app: AppSession = Depends(get_app_session)):
    ctx = get_active_play_context(app)
    char_id = ctx.slot_id if ctx else None
    reset_deck(game_id=app.selected_game_id, char_id=char_id)
    if ctx:
        ctx.refresh_deck()
        store = get_play_store(app.selected_game_id)
        if store:
            store.persist_ctx(ctx)
    remaining = deck_remaining(_deck_scope(app, ctx))
    return {
        "remaining": remaining,
        "ok": True,
        "formatted": f"Deck reset and shuffled (**{remaining}** cards).",
    }


@router.post("/roll")
def quick_roll(body: RollRequest, app: AppSession = Depends(get_app_session)):
    ctx = get_active_play_context(app)
    char_id = ctx.slot_id if ctx else None
    result = roll_dice(body.expression)
    formatted = format_dice_result(result)
    messages = list(get_messages(app))
    messages.append({"role": "assistant", "content": formatted})
    sync_messages_to_context(app, messages)
    store = get_play_store(app.selected_game_id)
    if char_id and result.get("ok") and store:
        store.log_roll(char_id, "", result=result, ctx=ctx)
        if ctx:
            store.persist_ctx(ctx)
    return {"result": result, "formatted": formatted, "messages": messages}
