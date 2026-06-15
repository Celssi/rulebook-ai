"""Play handlers (domain layer)."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history
from src.retrieval_profiles import resolve_retrieval_profile
GAME_ID = "lighthouse"
from src.games.lighthouse.actions import SHORTCUT_IDS, match_lighthouse_shortcut, run_shortcut
from src.games.lighthouse.curated import weather_options
from src.games.lighthouse.lonelog import (
    log_narrative_line,
    log_task_draw,
    narrative_context_for_ai,
    read_tail,
)
from src.games.lighthouse.narrator import synthesize_logbook_entry, synthesize_lonelog_summary
from src.games.lighthouse.roster import create_watch, delete_watch, list_watches, load_watch, save_watch
from src.games.lighthouse.watch import (
    KeeperWatch,
    format_summary,
    watch_from_dict,
    watch_to_dict,
)
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.llm import ChatProvider
# rag_query is imported lazily at the call site (avoids src.rag <-> registry cycle).


def _store():
    return get_play_store(GAME_ID)


def get_watch(ctx: PlayContext) -> KeeperWatch:
    return watch_from_dict(ctx.entity or {})


def persist_watch(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    watch = watch_from_dict(raw)
    watch.clamp()
    if ctx.slot_id:
        watch.id = ctx.slot_id
    ctx.entity = watch_to_dict(watch)
    save_watch(watch)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str]:
    store = _store()
    if not store:
        return "virtual", "player"
    settings = store.get_settings_ctx(ctx)
    return settings.get("card_source", "virtual"), settings.get("story_mode", "player")


def shortcut_kwargs(ctx: PlayContext) -> dict:
    watch = get_watch(ctx)
    card_source, _ = get_play_settings(ctx)
    return {
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
        "weather_mood": watch.weather_mood,
    }


def watch_header(ctx: PlayContext) -> dict:
    watch = get_watch(ctx)
    _, story_mode = get_play_settings(ctx)
    return {
        "summary": format_summary(watch),
        "name": watch.name,
        "night_count": watch.night_count,
        "weather_mood": watch.weather_mood,
        "lamp_lit": watch.lamp_lit,
        "last_task": watch.last_task,
        "story_mode": story_mode,
    }


def watch_options_payload() -> dict:
    return {"weather_moods": weather_options()}


def roster_payload() -> list[dict]:
    return [{"id": e.id, "name": e.name.strip()} for e in list_watches()]


def create_watch_entry(name: str) -> dict:
    watch = create_watch(name)
    return watch_to_dict(watch) if hasattr(watch, "id") else dict(watch)


def delete_watch_entry(watch_id: str) -> None:
    delete_watch(watch_id)


def switch_watch(app: AppSession, watch_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Lighthouse store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, watch_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_watch(ctx: PlayContext) -> dict:
    watch = KeeperWatch(id=ctx.slot_id or "")
    ctx.entity = watch_to_dict(watch)
    save_watch(watch)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def _answer_prompt(
    prompt: str,
    ctx: PlayContext,
    *,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
    chat_provider: ChatProvider,
) -> tuple[str, list[dict]]:
    from src.rag import query as rag_query

    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions or None,
        game_id=GAME_ID,
        play_entity=watch_to_dict(get_watch(ctx)),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    return result.answer, result.sources


def _maybe_ai_prose(
    ctx: PlayContext,
    watch: KeeperWatch,
    mechanics: str,
    *,
    chat_provider: ChatProvider,
) -> str | None:
    _, story_mode = get_play_settings(ctx)
    if story_mode != "ai_narrator":
        return None
    try:
        story_so_far = narrative_context_for_ai(ctx.slot_id) if ctx.slot_id else ""
        prose = synthesize_logbook_entry(
            mechanics,
            keeper_name=watch.name,
            night=watch.night_count,
            story_so_far=story_so_far,
            chat_provider=chat_provider,
        )
        if prose and ctx.slot_id:
            try:
                summary = synthesize_lonelog_summary(prose, chat_provider=chat_provider)
                if summary:
                    log_narrative_line(ctx.slot_id, summary)
            except Exception:
                pass
        return prose
    except Exception:
        return None


_NARRATOR_SHORTCUTS = frozenset(
    {"maintenance", "observation", "event", "light_lamp", "beachcombing"}
)


def _apply_shortcut_state(ctx: PlayContext, run: dict) -> None:
    watch = get_watch(ctx)
    task = run.get("task")
    if task:
        watch.last_task = str(task)
    cards = run.get("cards")
    if cards:
        watch.last_cards = list(cards)
    if run.get("lamp_lit") is True:
        watch.lamp_lit = True
    if task == "beachcombing" and run.get("finds"):
        for f in run["finds"]:
            item = str(f.get("item", "")).strip()
            if item:
                watch.inventory_notes.append(item[:120])
        watch.inventory_notes = watch.inventory_notes[-20:]
    ctx.entity = watch_to_dict(watch)
    save_watch(watch)
    if ctx.slot_id and cards:
        label = str(task or "draw").replace("_", " ")
        log_task_draw(ctx.slot_id, label, list(cards))


def run_watch_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
    beachcombing_hour: int | None = None,
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in SHORTCUT_IDS:
        raise ValueError(f"Unknown Lighthouse shortcut: {shortcut_id}")

    route = f"lighthouse:{shortcut_id}"
    kwargs = shortcut_kwargs(ctx)
    if beachcombing_hour is not None:
        kwargs["beachcombing_hour"] = beachcombing_hour

    run = run_shortcut(shortcut_id, game_id=GAME_ID, **kwargs)
    user_message = run["user_message"]
    watch = get_watch(ctx)
    sources: list[dict] = []

    if shortcut_id in _NARRATOR_SHORTCUTS:
        prose = _maybe_ai_prose(ctx, watch, user_message, chat_provider=chat_provider)
        if prose:
            answer = prose
        elif run.get("static"):
            answer = user_message
        else:
            rag_answer, sources = _answer_prompt(
                run["prompt"],
                ctx,
                retrieval_cfg=retrieval_cfg,
                top_k=top_k,
                factions=factions,
                chat_provider=chat_provider,
            )
            answer = f"{user_message}\n\n{rag_answer}"
    elif run.get("static"):
        answer = user_message
    elif shortcut_id == "rules_help":
        rag_answer, sources = _answer_prompt(
            run["prompt"],
            ctx,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            factions=factions,
            chat_provider=chat_provider,
        )
        answer = f"{user_message}\n\n{rag_answer}"
    else:
        answer = user_message

    _apply_shortcut_state(ctx, run)
    if run.get("dice") and ctx.slot_id:
        store = _store()
        if store:
            store.log_roll(ctx.slot_id, "", result=run["dice"], ctx=ctx)
    ctx.refresh_deck()
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return user_message, answer, sources, route


def execute_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
    beachcombing_hour: int | None = None,
) -> tuple[str, str, list[dict], str]:
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    _ = prior_history or recent_chat_history(ctx.messages)
    return run_watch_shortcut(
        ctx,
        shortcut_id,
        chat_provider=app.chat_provider,
        retrieval_cfg=retrieval_cfg,
        top_k=app.top_k,
        factions=app.selected_factions,
        beachcombing_hour=beachcombing_hour,
    )




def try_handle_prompt(
    ctx: PlayContext,
    prompt: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, list[dict], str] | None:
    shortcut_id = match_lighthouse_shortcut(prompt)
    if not shortcut_id:
        return None
    return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]


def shortcuts_payload() -> list[dict]:
    from src.games.lighthouse.actions import SHORTCUTS

    return [dict(s) for s in SHORTCUTS]


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines)
