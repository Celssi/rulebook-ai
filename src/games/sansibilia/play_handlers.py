"""Play handlers (domain layer)."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history
from src.retrieval_profiles import resolve_retrieval_profile
GAME_ID = "sansibilia"
from src.games.sansibilia.actions import SHORTCUT_IDS, match_sansibilia_shortcut, run_shortcut, shortcuts_for_visit
from src.games.sansibilia.curated import (
    character_role_options,
    character_trait_options,
    ending_mode_options,
    format_character_archetype,
    format_character_draw,
    format_day_draw,
    lookup_character_role,
    lookup_character_trait,
    parse_playing_card,
    score_for_turn,
)
from src.games.sansibilia.lonelog import (
    log_city_change,
    log_day_draw,
    log_narrative,
    log_player_action,
    narrative_context_for_ai,
    open_day,
    read_tail,
)
from src.games.sansibilia.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.sansibilia.roster import create_visit, delete_visit, list_visits, load_visit
from src.games.sansibilia.visit import (
    SansibiliaVisit,
    format_summary,
    save_visit,
    visit_from_dict,
    visit_to_dict,
)
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.llm import ChatProvider
# rag_query is imported lazily at the call site (avoids src.rag <-> registry cycle).
from src.tools import draw_cards


def _store():
    return get_play_store(GAME_ID)


def get_visit(ctx: PlayContext) -> SansibiliaVisit:
    return visit_from_dict(ctx.entity or {})


def persist_visit(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    visit = visit_from_dict(raw)
    visit.clamp()
    if visit.character_trait_rank and visit.character_role_rank:
        visit.archetype = format_character_archetype(
            lookup_character_trait(visit.character_trait_rank),
            lookup_character_role(visit.character_role_rank),
        )
    if ctx.slot_id:
        visit.id = ctx.slot_id
    ctx.entity = visit_to_dict(visit)
    save_visit(visit)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str, str]:
    store = _store()
    if not store:
        return "four_changes", "virtual", "player"
    settings = store.get_settings_ctx(ctx)
    ending = settings.get("ending_mode", "four_changes")
    card_source = settings.get("card_source", "virtual")
    story_mode = settings.get("story_mode", "player")
    return ending, card_source, story_mode


def shortcut_kwargs(ctx: PlayContext) -> dict:
    visit = get_visit(ctx)
    ending_mode, card_source, _ = get_play_settings(ctx)
    if ending_mode == "score_90":
        visit.ending_mode = "score_90"
    return {
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
        "ending_mode": ending_mode,
        "ace_value": visit.ace_value,
        "visit_day": visit.visit_day,
    }


def log_user_prompt(ctx: PlayContext, prompt: str) -> None:
    if not ctx.slot_id:
        return
    stripped = prompt.strip()
    if stripped.startswith("@"):
        log_player_action(ctx.slot_id, stripped)


def visit_header(ctx: PlayContext) -> dict:
    visit = get_visit(ctx)
    ending_mode, _, _ = get_play_settings(ctx)
    visit.ending_mode = ending_mode
    return {
        "summary": format_summary(visit),
        "name": visit.name,
        "archetype": visit.archetype,
        "visit_day": visit.visit_day,
        "city_changes": visit.city_changes,
        "ending_mode": visit.ending_mode,
        "score_total": visit.score_total,
        "ace_value": visit.ace_value,
        "visit_complete": visit.is_ended(),
        "last_adjective": visit.last_adjective,
        "last_location_event": visit.last_location_event,
    }


def visit_options_payload() -> dict:
    return {
        "ending_modes": ending_mode_options(),
        "character_traits": character_trait_options(),
        "character_roles": character_role_options(),
    }


def roster_payload() -> list[dict]:
    entries: list[dict] = []
    for entry in list_visits():
        visit = load_visit(entry.id)
        name = visit.name.strip() if hasattr(visit, "name") else str(visit.get("name", "") or "").strip()
        entries.append({"id": entry.id, "name": name})
    return entries


def create_visit_entry(name: str) -> dict:
    visit = create_visit(name)
    return visit_to_dict(visit) if hasattr(visit, "id") else dict(visit)


def delete_visit_entry(visit_id: str) -> None:
    delete_visit(visit_id)


def switch_visit(app: AppSession, visit_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("San Sibilia store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, visit_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_visit(ctx: PlayContext) -> dict:
    visit = SansibiliaVisit(id=ctx.slot_id or "")
    ending_mode, _, _ = get_play_settings(ctx)
    visit.ending_mode = ending_mode
    ctx.entity = visit_to_dict(visit)
    save_visit(visit)
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
    visit = get_visit(ctx)
    _, card_source, _ = get_play_settings(ctx)
    from src.rag import query as rag_query

    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions or None,
        game_id=GAME_ID,
        play_entity=visit_to_dict(visit),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    _ = card_source
    return result.answer, result.sources


def draw_character_table(ctx: PlayContext) -> dict:
    visit = get_visit(ctx)
    _, card_source, _ = get_play_settings(ctx)
    if card_source == "physical":
        raise ValueError("Physical deck mode: enter cards manually in Settings.")
    ctx.sync_deck()
    result = draw_cards(count=2, game_id=GAME_ID, char_id=ctx.slot_id or None)
    ctx.refresh_deck()
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    cards = list(result["cards"] or [])
    drawn = format_character_draw(cards)
    visit.character_cards = cards
    visit.character_trait_rank = str(drawn.get("trait_rank") or "")
    visit.character_role_rank = str(drawn.get("role_rank") or "")
    visit.character_rank = ""
    visit.archetype = str(drawn.get("archetype") or "")
    ctx.entity = visit_to_dict(visit)
    save_visit(visit)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {"cards": cards, **drawn}


def draw_day_cards(ctx: PlayContext) -> dict:
    visit = get_visit(ctx)
    if visit.is_ended():
        raise ValueError("Visit has ended — use ending journal prompts.")
    ending_mode, card_source, _ = get_play_settings(ctx)
    visit.ending_mode = ending_mode
    if card_source == "physical":
        raise ValueError("Physical deck mode: report cards in chat.")
    ctx.sync_deck()
    result = draw_cards(count=2, game_id=GAME_ID, char_id=ctx.slot_id or None)
    ctx.refresh_deck()
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    cards = list(result["cards"] or [])
    day = format_day_draw(cards[0], cards[1])
    visit.last_cards = cards
    visit.last_adjective = day["adjective"]
    visit.last_location_event = day["location_event"]
    turn_score = 0
    if visit.ending_mode == "score_90":
        turn_score = score_for_turn(cards, ace_value=visit.ace_value)
        visit.score_total += turn_score
    if visit.is_ended():
        visit.visit_complete = True
    ctx.entity = visit_to_dict(visit)
    save_visit(visit)
    if ctx.slot_id:
        log_day_draw(
            ctx.slot_id,
            visit,
            cards[0],
            cards[1],
            day["adjective"],
            day["location_event"],
        )
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {
        "cards": cards,
        "turn_score": turn_score,
        "city_change": day.get("city_change"),
        "visit_complete": visit.is_ended(),
        **day,
    }


def record_city_change(ctx: PlayContext, note: str = "") -> dict:
    visit = get_visit(ctx)
    if visit.city_changes >= 4:
        raise ValueError("All four city-change boxes are already checked.")
    change = None
    if len(visit.last_cards) >= 2:
        from src.games.sansibilia.curated import detect_city_change

        change = detect_city_change(visit.last_cards[0], visit.last_cards[1])
    visit.city_changes += 1
    if note.strip():
        visit.city_change_notes.append(note.strip())
    elif change:
        visit.city_change_notes.append(str(change.get("title") or "City change"))
    if visit.ending_mode == "four_changes" and visit.city_changes >= 4:
        visit.visit_complete = True
    ctx.entity = visit_to_dict(visit)
    save_visit(visit)
    if ctx.slot_id and change:
        log_city_change(
            ctx.slot_id,
            str(change.get("title") or "City change"),
            str(change.get("prompt") or note),
        )
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {
        "city_changes": visit.city_changes,
        "visit_complete": visit.is_ended(),
        "change": change,
    }


def advance_day(ctx: PlayContext, days_between: int | None = None) -> dict:
    visit = get_visit(ctx)
    visit.visit_day += 1
    if days_between is not None:
        visit.days_between = days_between
    visit.last_cards = []
    visit.last_adjective = ""
    visit.last_location_event = ""
    ctx.entity = visit_to_dict(visit)
    save_visit(visit)
    if ctx.slot_id:
        open_day(ctx.slot_id, visit)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {"visit_day": visit.visit_day}


def format_day_draw_message(visit: SansibiliaVisit, day: dict[str, Any]) -> str:
    user_message = (
        f"**Day {visit.visit_day} draw:** {day['card1']} · {day['card2']}\n\n"
        f"**{day['adjective']}** + **{day['location_event']}**"
    )
    if day.get("city_change"):
        ch = day["city_change"]
        user_message += f"\n\n**City change!** {ch['title']}\n{ch['prompt']}"
    if day.get("turn_score"):
        user_message += f"\n\nScore +{day['turn_score']} (total {visit.score_total})"
    return user_message


def _journal_context(visit: SansibiliaVisit, day: dict[str, Any]) -> str:
    lines = [
        f"Prompt: {day['adjective']} {day['location_event']}",
        f"Cards: {day['card1']} (adjective), {day['card2']} (location/event)",
    ]
    if day.get("city_change"):
        ch = day["city_change"]
        lines.append(f"City change: {ch['title']} — {ch['prompt']}")
    if day.get("turn_score"):
        lines.append(f"Score +{day['turn_score']} (total {visit.score_total})")
    return "\n".join(lines)


def generate_ai_journal(
    ctx: PlayContext,
    visit: SansibiliaVisit,
    day: dict[str, Any],
    *,
    chat_provider: ChatProvider,
) -> str | None:
    """Long journal prose for chat; compact => summary for lonelog."""
    _, _, story_mode = get_play_settings(ctx)
    if story_mode != "ai_narrator":
        return None
    try:
        story_so_far = narrative_context_for_ai(ctx.slot_id) if ctx.slot_id else ""
        prose = synthesize_journal_entry(
            _journal_context(visit, day),
            visit_name=visit.name,
            archetype=visit.archetype,
            visit_day=visit.visit_day,
            story_so_far=story_so_far,
            chat_provider=chat_provider,
        )
        if not prose:
            return None
        if ctx.slot_id:
            try:
                summary = synthesize_lonelog_summary(prose, chat_provider=chat_provider)
                if summary:
                    log_narrative(ctx.slot_id, summary)
            except Exception:
                pass
        return prose
    except Exception:
        return None


def build_day_draw_answer(
    ctx: PlayContext,
    day: dict[str, Any],
    *,
    chat_provider: ChatProvider,
) -> str:
    visit = get_visit(ctx)
    prose = generate_ai_journal(ctx, visit, day, chat_provider=chat_provider)
    if prose:
        return prose
    return format_day_draw_message(visit, day)


def perform_day_draw(
    ctx: PlayContext,
    *,
    chat_provider: ChatProvider,
) -> tuple[dict[str, Any], str, str]:
    """Draw day cards, build chat messages. Mutates ctx visit state."""
    day = draw_day_cards(ctx)
    visit = get_visit(ctx)
    user_message = format_day_draw_message(visit, day)
    answer = build_day_draw_answer(ctx, day, chat_provider=chat_provider)
    return day, user_message, answer




def shortcuts_payload(ctx: PlayContext) -> list[dict]:
    visit = get_visit(ctx)
    return [dict(s) for s in shortcuts_for_visit(visit_complete=visit.is_ended())]


def execute_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, str, list[dict], str]:
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    _ = prior_history or recent_chat_history(ctx.messages)
    return run_visit_shortcut(
        ctx,
        shortcut_id,
        chat_provider=app.chat_provider,
        retrieval_cfg=retrieval_cfg,
        top_k=app.top_k,
        factions=app.selected_factions,
    )


def run_visit_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in SHORTCUT_IDS:
        raise ValueError(f"Unknown San Sibilia shortcut: {shortcut_id}")

    route = f"sansibilia:{shortcut_id}"
    store = _store()

    if shortcut_id == "draw_character":
        drawn = draw_character_table(ctx)
        user_message = (
            f"**Character draw:** {drawn['card1']} (trait) · {drawn['card2']} (role)\n\n"
            f"**{drawn.get('archetype', '')}**"
        )
        if store:
            store.persist_ctx(ctx)
        return user_message, user_message, [], route

    if shortcut_id == "draw_day":
        _, user_message, answer = perform_day_draw(ctx, chat_provider=chat_provider)
        if store:
            store.persist_ctx(ctx)
        return user_message, answer, [], route

    run = run_shortcut(shortcut_id, **shortcut_kwargs(ctx))
    user_message = run["user_message"]

    if shortcut_id == "roll_days_between" and run.get("dice") and ctx.slot_id and store:
        store.log_roll(ctx.slot_id, "", result=run["dice"], ctx=ctx)

    if run.get("static"):
        if store:
            store.persist_ctx(ctx)
        return user_message, user_message, [], route

    answer, sources = _answer_prompt(
        run["prompt"],
        ctx,
        retrieval_cfg=retrieval_cfg,
        top_k=top_k,
        factions=factions,
        chat_provider=chat_provider,
    )
    ctx.refresh_deck()
    if store:
        store.persist_ctx(ctx)
    return user_message, f"{user_message}\n\n{answer}", sources, route


def try_handle_prompt(
    ctx: PlayContext,
    prompt: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, list[dict], str] | None:
    shortcut_id = match_sansibilia_shortcut(prompt)
    if not shortcut_id:
        return None
    return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines)
