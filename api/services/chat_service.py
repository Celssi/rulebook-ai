"""Chat routing for API (extracted from streamlit_app._answer_user_prompt)."""

from __future__ import annotations

from api.services import brambletrek_service as bt
from api.services.session_service import default_factions, get_active_play_context, get_messages, sync_messages_to_context
from api.utils import RETRIEVAL_PROFILES, recent_chat_history, resolve_retrieval_profile, to_langchain_history
from src.agent import run_agent
from src.config import GAME_BRAMBLETREK
from src.games.registry import get_game_plugin
from src.games.saves import AppSession, get_play_store
from src.games.warhammer_40k.state import game_state_from_dict
from src.llm import ChatProvider
from src.rag import query as rag_query
from src.tools import (
    draw_cards,
    extract_dice_expression,
    format_card_result,
    format_dice_result,
    is_ai_draw_request,
    is_card_plus_rules_question,
    is_card_question,
    is_dice_question,
    is_physical_card_report,
    normalize_card_name,
    register_physical_card,
    roll_dice,
    run_explicit_command,
)


def answer_user_prompt(
    app: AppSession,
    prompt: str,
) -> tuple[str, list[dict], str]:
    game_id = app.selected_game_id
    plugin = get_game_plugin(game_id)
    ctx = get_active_play_context(app)
    char_id = ctx.slot_id if ctx else None
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    top_k = app.top_k
    selected_factions = default_factions(app)
    chat_provider = app.chat_provider
    prior_history = recent_chat_history(get_messages(app))

    if ctx:
        ctx.sync_deck()

    if plugin and plugin.has_character_sheet and char_id and ctx:
        bt.log_user_prompt(ctx, prompt)

    store = get_play_store(game_id)

    cmd = run_explicit_command(prompt, game_id=game_id, char_id=char_id)
    if cmd is not None:
        if cmd.get("route") == "log" and char_id and store:
            store.append_log(char_id, cmd.get("log_text", ""), ctx=ctx)
        tr = cmd.get("tool_result")
        if char_id and tr and store:
            if cmd.get("route") == "dice" and tr.get("ok"):
                store.log_roll(char_id, "", result=tr, ctx=ctx)
            elif cmd.get("route") == "cards" and tr.get("ok") and tr.get("cards"):
                store.log_draw(char_id, tr["cards"], ctx=ctx)
        if ctx:
            ctx.refresh_deck()
            store.persist_ctx(ctx) if store else None
        return cmd.get("answer", ""), cmd.get("sources", []), cmd.get("route", "command")

    story_mode, card_source = ("player", "virtual")
    if ctx:
        story_mode, card_source = bt.get_play_settings(ctx)

    if plugin and plugin.has_character_sheet and ctx:
        handled = bt.try_handle_prompt(ctx, prompt, app=app, prior_history=prior_history)
        if handled is not None:
            ctx.refresh_deck()
            if store:
                store.persist_ctx(ctx)
            return handled

    game_state = None
    if plugin and plugin.has_game_state:
        game_state = game_state_from_dict(app.game_state_40k)

    if app.mode == "Agent":
        out = run_agent(
            prompt,
            history=to_langchain_history(prior_history),
            game_state=game_state,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=ctx.entity if ctx else None,
            chat_provider=chat_provider,
            char_id=char_id,
            story_mode=story_mode,
            card_source=card_source,
        )
        if ctx:
            ctx.refresh_deck()
            if store:
                store.persist_ctx(ctx)
        return out["answer"], out.get("sources", []), out.get("route", "")

    if is_card_plus_rules_question(prompt):
        out = run_agent(
            prompt,
            history=to_langchain_history(prior_history),
            game_state=game_state,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=ctx.entity if ctx else None,
            chat_provider=chat_provider,
            char_id=char_id,
            story_mode=story_mode,
            card_source=card_source,
        )
        if ctx:
            ctx.refresh_deck()
            if store:
                store.persist_ctx(ctx)
        return out["answer"], out.get("sources", []), out.get("route", "card_rag")

    if is_dice_question(prompt):
        expr = extract_dice_expression(prompt) or "d6"
        result = roll_dice(expr)
        if char_id and result.get("ok") and store:
            store.log_roll(char_id, "", result=result, ctx=ctx)
            if ctx and store:
                store.persist_ctx(ctx)
        return format_dice_result(result), [], "dice"

    if is_card_question(prompt):
        if card_source == "physical" and not is_ai_draw_request(prompt):
            if normalize_card_name(prompt) or is_physical_card_report(prompt):
                result = register_physical_card(prompt, game_id=game_id, char_id=char_id)
                if char_id and result.get("ok") and result.get("cards") and store:
                    store.log_draw(char_id, result["cards"], label="Physical draw", ctx=ctx)
            else:
                return (
                    "Physical deck mode: draw from your real deck and report the card "
                    "(e.g. Queen of Hearts), or ask to 'draw a card for me' for a virtual draw.",
                    [],
                    "cards",
                )
        else:
            result = draw_cards(count=1, game_id=game_id, char_id=char_id)
            if char_id and result.get("ok") and result.get("cards") and store:
                store.log_draw(char_id, result["cards"], ctx=ctx)
        if ctx:
            ctx.refresh_deck()
            if store:
                store.persist_ctx(ctx)
        return format_card_result(result), [], "cards"

    factions = selected_factions if selected_factions else None
    bt_char = bt.get_character(ctx) if ctx and plugin and plugin.has_character_sheet else None
    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions,
        game_state=game_state,
        game_id=game_id,
        chat_history=prior_history,
        candidate_k=retrieval_cfg["candidate_k"],
        use_hybrid=retrieval_cfg["use_hybrid"],
        use_rerank=retrieval_cfg.get("use_rerank", False),
        brambletrek_character=bt_char,
        chat_provider=chat_provider,
    )
    if ctx and store:
        store.persist_ctx(ctx)
    return result.answer, result.sources, "rag"


def send_chat(app: AppSession, prompt: str) -> dict:
    messages = list(get_messages(app))
    messages.append({"role": "user", "content": prompt})
    answer, sources, route = answer_user_prompt(app, prompt)
    messages.append({"role": "assistant", "content": answer})
    app.last_sources = sources
    sync_messages_to_context(app, messages)
    ctx = get_active_play_context(app)
    if ctx:
        store = get_play_store(app.selected_game_id)
        if store:
            store.persist_ctx(ctx)
    return {"answer": answer, "sources": sources, "route": route, "messages": messages}
