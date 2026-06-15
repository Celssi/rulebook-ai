"""Play handlers (domain layer)."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history
from src.retrieval_profiles import resolve_retrieval_profile
GAME_ID = "apothecaria"
from src.games.apothecaria.actions import SHORTCUT_IDS, match_apothecaria_shortcut, run_shortcut, shortcuts_for_cottage
from src.games.apothecaria.curated import (
    all_purchasable_tools,
    all_upgrades,
    locale_meta,
    locale_options,
    village_services,
)
from src.games.apothecaria.game_logic import (
    advance_downtime,
    advance_week,
    buy_tool,
    buy_upgrade,
    change_locale,
    complete_potion,
    foraging_points_for_locale,
    potion_totals,
    set_hunt_target,
)
from src.games.apothecaria.lonelog import log_draw, log_narrative, narrative_context_for_ai, read_tail
from src.games.apothecaria.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.apothecaria.roster import create_cottage, delete_cottage, list_cottages, load_cottage, save_cottage
from src.games.apothecaria.cottage import (
    WitchCottage,
    cottage_from_dict,
    cottage_to_dict,
    format_summary,
)
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.llm import ChatProvider
# rag_query is imported lazily at the call site (avoids src.rag <-> registry cycle).


def _store():
    return get_play_store(GAME_ID)


def log_user_prompt(ctx: PlayContext, prompt: str) -> None:
    if not ctx.slot_id:
        return
    from src.games.apothecaria.lonelog import log_player_action

    stripped = prompt.strip()
    if stripped.startswith("@"):
        log_player_action(ctx.slot_id, stripped)


def get_cottage(ctx: PlayContext) -> WitchCottage:
    return cottage_from_dict(ctx.entity or {})


def persist_cottage(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    cottage = cottage_from_dict(raw)
    cottage.clamp()
    if ctx.slot_id:
        cottage.id = ctx.slot_id
    ctx.entity = cottage_to_dict(cottage)
    save_cottage(cottage)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str]:
    store = _store()
    if not store:
        return "virtual", "player"
    settings = store.get_settings_ctx(ctx)
    return settings.get("card_source", "virtual"), settings.get("story_mode", "player")


def shortcut_kwargs(ctx: PlayContext, **extra: Any) -> dict:
    cottage = get_cottage(ctx)
    card_source, _ = get_play_settings(ctx)
    return {
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
        "reputation": cottage.reputation,
        "current_locale": cottage.current_locale,
        "ailment_tags": list(cottage.ailment_tags),
        "cottage": cottage,
        **extra,
    }


def cottage_header(ctx: PlayContext) -> dict:
    cottage = get_cottage(ctx)
    _, story_mode = get_play_settings(ctx)
    poison, sweet = potion_totals(cottage)
    return {
        "summary": format_summary(cottage),
        "name": cottage.name,
        "reputation": cottage.reputation,
        "silver": cottage.silver,
        "season": cottage.season,
        "week": cottage.week,
        "phase": cottage.phase,
        "downtime_timer": cottage.downtime_timer,
        "foraging_points": foraging_points_for_locale(cottage),
        "current_locale": cottage.current_locale,
        "patient_name": cottage.patient_name,
        "patient_type": cottage.patient_type,
        "ailment_name": cottage.ailment_name,
        "ailment_tags": cottage.ailment_tags,
        "ailment_timer": cottage.ailment_timer,
        "hunting_reagent": cottage.hunting_reagent,
        "hunting_fv": cottage.hunting_fv,
        "inventory_count": len(cottage.inventory),
        "potion_poison": poison,
        "potion_sweet": sweet,
        "familiar_type": cottage.familiar_type,
        "familiar_skill": cottage.familiar_skill,
        "tools_owned": list(cottage.tools_owned),
        "upgrades_owned": list(cottage.upgrades_owned),
        "story_mode": story_mode,
    }


def cottage_options_payload() -> dict:
    return {
        "locales": locale_options(),
        "locale_meta": locale_meta(),
        "tools": all_purchasable_tools(),
        "upgrades": all_upgrades(),
        "village": village_services(),
    }


def roster_payload() -> list[dict]:
    return [{"id": e.id, "name": e.name.strip()} for e in list_cottages()]


def create_cottage_entry(name: str) -> dict:
    cottage = create_cottage(name)
    return cottage_to_dict(cottage) if hasattr(cottage, "id") else dict(cottage)


def delete_cottage_entry(cottage_id: str) -> None:
    delete_cottage(cottage_id)


def switch_cottage(app: AppSession, cottage_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Apothecaria store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, cottage_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_cottage(ctx: PlayContext) -> dict:
    cottage = WitchCottage(id=ctx.slot_id or "")
    ctx.entity = cottage_to_dict(cottage)
    save_cottage(cottage)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def _sync_cottage_from_run(ctx: PlayContext, cottage: WitchCottage, run: dict) -> None:
    ctx.entity = cottage_to_dict(cottage)
    save_cottage(cottage)


def change_locale_action(ctx: PlayContext, locale_id: str) -> dict:
    cottage = get_cottage(ctx)
    result = change_locale(cottage, locale_id)
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return result


def hunt_reagent_action(ctx: PlayContext, reagent_name: str) -> dict:
    cottage = get_cottage(ctx)
    result = set_hunt_target(cottage, reagent_name)
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return result


def complete_potion_action(ctx: PlayContext) -> dict:
    cottage = get_cottage(ctx)
    poison, sweet = potion_totals(cottage)
    result = complete_potion(cottage, poison, sweet)
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {"poison": poison, "sweet": sweet, **result}


def advance_week_action(ctx: PlayContext) -> dict:
    cottage = get_cottage(ctx)
    result = advance_week(cottage, downtime=cottage.phase == "downtime")
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return result


def advance_downtime_action(ctx: PlayContext) -> dict:
    cottage = get_cottage(ctx)
    result = advance_downtime(cottage)
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return result


def buy_tool_action(ctx: PlayContext, tool_id: str) -> dict:
    cottage = get_cottage(ctx)
    result = buy_tool(cottage, tool_id)
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return result


def buy_upgrade_action(ctx: PlayContext, upgrade_id: str) -> dict:
    cottage = get_cottage(ctx)
    result = buy_upgrade(cottage, upgrade_id)
    _sync_cottage_from_run(ctx, cottage, {})
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return result


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
        play_entity=cottage_to_dict(get_cottage(ctx)),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    return result.answer, result.sources


def _maybe_ai_prose(
    ctx: PlayContext,
    cottage: WitchCottage,
    context: str,
    *,
    chat_provider: ChatProvider,
) -> str | None:
    _, story_mode = get_play_settings(ctx)
    if story_mode != "ai_narrator":
        return None
    try:
        story_so_far = narrative_context_for_ai(ctx.slot_id) if ctx.slot_id else ""
        prose = synthesize_journal_entry(
            context,
            witch_name=cottage.name,
            week=cottage.week,
            season=cottage.season,
            story_so_far=story_so_far,
            chat_provider=chat_provider,
        )
        if prose and ctx.slot_id:
            try:
                summary = synthesize_lonelog_summary(prose, chat_provider=chat_provider)
                if summary:
                    log_narrative(ctx.slot_id, summary)
            except Exception:
                pass
        return prose or None
    except Exception:
        return None


_NARRATOR_SHORTCUTS = frozenset({"draw_ailment", "forage_event", "start_patient", "witch_clue"})


def _apply_shortcut_state(ctx: PlayContext, shortcut_id: str, run: dict, cottage: WitchCottage) -> None:
    cards = run.get("cards") or []
    if cards:
        cottage.last_cards = list(cards)
    cottage.last_draw_kind = shortcut_id
    draw = run.get("draw_result") or {}

    if shortcut_id == "draw_patient_type":
        cottage.patient_type = str(draw.get("patient_type", ""))
    elif shortcut_id == "draw_ailment":
        cottage.ailment_name = str(draw.get("name", ""))
        cottage.ailment_tags = list(draw.get("tags") or [])
        timer = draw.get("timer")
        cottage.ailment_timer = int(timer) if timer is not None else None
        cottage.phase = "ailment"
    elif shortcut_id == "start_patient":
        patient = draw.get("patient") or {}
        ailment = draw.get("ailment") or {}
        cottage.patient_type = str(patient.get("patient_type", ""))
        cottage.ailment_name = str(ailment.get("name", ""))
        cottage.ailment_tags = list(ailment.get("tags") or [])
        timer = ailment.get("timer")
        cottage.ailment_timer = int(timer) if timer is not None else None
        cottage.phase = "ailment"
        cottage.turn_count = 0
        cottage.foraging_tracks = {}
        cottage.seen_events = []
        cottage.hunting_reagent = ""
        cottage.hunting_fv = None
        cottage.current_locale = "glimmerwood"
    elif shortcut_id == "draw_familiar_type":
        cottage.familiar_type = str(draw.get("familiar_type", ""))
    elif shortcut_id == "draw_familiar_skill":
        cottage.familiar_skill = str(draw.get("familiar_skill", ""))
    elif shortcut_id == "witch_clue":
        cottage.joker_clues = int(cottage.joker_clues or 0) + 1
    elif shortcut_id == "forage_event":
        if draw.get("timer") is not None:
            cottage.ailment_timer = draw.get("timer")
        if cottage.ailment_timer == 0 and cottage.ailment_name:
            cottage.phase = "consequence"

    _sync_cottage_from_run(ctx, cottage, run)

    if ctx.slot_id and cards:
        detail = str(
            draw.get("name")
            or draw.get("event")
            or draw.get("summary")
            or draw.get("clue")
            or ""
        )[:120]
        log_draw(ctx.slot_id, shortcut_id.replace("_", " "), cards[0], detail)


def run_cottage_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
    params: dict | None = None,
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in SHORTCUT_IDS:
        raise ValueError(f"Unknown Apothecaria shortcut: {shortcut_id}")

    route = f"apothecaria:{shortcut_id}"
    ctx.sync_deck()
    cottage = get_cottage(ctx)
    run = run_shortcut(shortcut_id, game_id=GAME_ID, **shortcut_kwargs(ctx, **(params or {})))
    user_message = run["user_message"]
    sources: list[dict] = []

    rag_shortcuts = {
        "locales_help",
        "reagents_help",
    }

    narrator_shortcuts = _NARRATOR_SHORTCUTS

    if run.get("static"):
        answer = user_message
    elif shortcut_id in narrator_shortcuts:
        prose = _maybe_ai_prose(ctx, cottage, run["prompt"], chat_provider=chat_provider)
        if prose:
            answer = prose
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
    elif shortcut_id in rag_shortcuts:
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

    _apply_shortcut_state(ctx, shortcut_id, run, cottage)
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
    params: dict | None = None,
) -> tuple[str, str, list[dict], str]:
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    _ = prior_history or recent_chat_history(ctx.messages)
    return run_cottage_shortcut(
        ctx,
        shortcut_id,
        chat_provider=app.chat_provider,
        retrieval_cfg=retrieval_cfg,
        top_k=app.top_k,
        factions=app.selected_factions,
        params=params,
    )




def try_handle_prompt(
    ctx: PlayContext,
    prompt: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, list[dict], str] | None:
    shortcut_id = match_apothecaria_shortcut(prompt)
    if not shortcut_id:
        return None
    return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]


def shortcuts_payload(ctx: PlayContext) -> list[dict]:
    cottage = get_cottage(ctx)
    return [
        dict(s)
        for s in shortcuts_for_cottage(
            phase=cottage.phase,
            has_ailment=bool(cottage.ailment_name),
            has_hunt=bool(cottage.hunting_reagent),
            has_inventory=bool(cottage.inventory),
        )
    ]


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines)
