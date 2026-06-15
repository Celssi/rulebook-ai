"""Whispers in the Walls business logic for API."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history
from src.retrieval_profiles import resolve_retrieval_profile
GAME_ID = "whispers"
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.games.whispers.actions import (
    SHORTCUT_IDS,
    match_whispers_shortcut,
    run_shortcut,
    shortcuts_for_investigation,
)
from src.games.whispers.curated import build_whispers_deck, format_card_draw, is_joker_card
from src.games.whispers.investigation import (
    WhispersInvestigation,
    format_summary,
    investigation_from_dict,
    investigation_to_dict,
    save_investigation,
)
from src.games.whispers.lonelog import (
    log_location_draw,
    log_narrative,
    log_player_action,
    log_whisper_draw,
    narrative_context_for_ai,
    open_investigation,
    read_tail,
)
from src.games.whispers.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.whispers.roster import create_investigation, delete_investigation, list_investigations, load_investigation
from src.llm import ChatProvider
# rag_query is imported lazily at the call site (avoids src.rag <-> registry cycle).
from src.tools import normalize_card_name


def _store():
    return get_play_store(GAME_ID)


def get_investigation(ctx: PlayContext) -> WhispersInvestigation:
    return investigation_from_dict(ctx.entity or {})


def persist_investigation(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    inv = investigation_from_dict(raw)
    inv.clamp()
    if ctx.slot_id:
        inv.id = ctx.slot_id
    ctx.entity = investigation_to_dict(inv)
    save_investigation(inv)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str, str]:
    store = _store()
    if not store:
        return "virtual", "player", "normal"
    settings = store.get_settings_ctx(ctx)
    card_source = settings.get("card_source", "virtual")
    story_mode = settings.get("story_mode", "player")
    difficulty = settings.get("difficulty", "normal")
    return card_source, story_mode, difficulty


def shortcut_kwargs(ctx: PlayContext) -> dict:
    inv = get_investigation(ctx)
    _, _, difficulty = get_play_settings(ctx)
    inv.difficulty = difficulty
    return {
        "difficulty": inv.difficulty,
        "extra_secrets": inv.extra_secrets,
        "whispers_deck": list(inv.whispers_deck),
        "jokers_drawn": inv.jokers_drawn,
    }


def log_user_prompt(ctx: PlayContext, prompt: str) -> None:
    if not ctx.slot_id:
        return
    stripped = prompt.strip()
    if stripped.startswith("@"):
        log_player_action(ctx.slot_id, stripped)


def investigation_header(ctx: PlayContext) -> dict:
    inv = get_investigation(ctx)
    _, _, difficulty = get_play_settings(ctx)
    inv.difficulty = difficulty
    return {
        "summary": format_summary(inv),
        "investigator_name": inv.investigator_name,
        "background": inv.background,
        "belonging": inv.belonging,
        "location_name": inv.location_name,
        "location_title": inv.location_title,
        "deck_built": inv.deck_built,
        "cards_remaining": inv.cards_remaining(),
        "turn_number": inv.turn_number,
        "jokers_drawn": inv.jokers_drawn,
        "difficulty": inv.difficulty,
        "investigation_complete": inv.is_ended(),
        "last_table": inv.last_table,
        "last_title": inv.last_title,
    }


def roster_payload() -> list[dict]:
    entries: list[dict] = []
    for entry in list_investigations():
        inv = load_investigation(entry.id)
        name = inv.investigator_name.strip() if hasattr(inv, "investigator_name") else ""
        if not name:
            name = str(inv.get("investigator_name", "") or "").strip()
        entries.append({"id": entry.id, "name": name})
    return entries


def create_investigation_entry(name: str) -> dict:
    inv = create_investigation(name)
    return investigation_to_dict(inv) if hasattr(inv, "id") else dict(inv)


def delete_investigation_entry(investigation_id: str) -> None:
    delete_investigation(investigation_id)


def switch_investigation(app: AppSession, investigation_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Whispers store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, investigation_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_investigation(ctx: PlayContext) -> dict:
    inv = WhispersInvestigation(id=ctx.slot_id or "")
    _, _, difficulty = get_play_settings(ctx)
    inv.difficulty = difficulty
    ctx.entity = investigation_to_dict(inv)
    save_investigation(inv)
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
    inv = get_investigation(ctx)
    from src.rag import query as rag_query

    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions or None,
        game_id=GAME_ID,
        play_entity=investigation_to_dict(inv),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    return result.answer, result.sources


def build_deck(ctx: PlayContext) -> dict[str, Any]:
    inv = get_investigation(ctx)
    if inv.deck_built and inv.whispers_deck:
        raise ValueError("Whispers deck already built — reset investigation to start over.")
    card_source, _, difficulty = get_play_settings(ctx)
    if card_source == "physical":
        raise ValueError("Physical deck mode: build your Whispers deck at the table, then report the location card.")
    inv.difficulty = difficulty
    deck = build_whispers_deck(difficulty=inv.difficulty, extra_secrets=inv.extra_secrets)
    location_card = deck[0]
    inv.whispers_deck = deck[1:]
    inv.discard_pile = [location_card]
    inv.deck_built = True
    inv.location_card = location_card
    draw = format_card_draw(location_card, is_location=True)
    inv.location_title = str(draw.get("title") or "")
    inv.last_card = location_card
    inv.last_table = "locations"
    inv.last_title = inv.location_title
    inv.last_prompt = str(draw.get("prompt") or "")
    ctx.entity = investigation_to_dict(inv)
    save_investigation(inv)
    if ctx.slot_id:
        open_investigation(ctx.slot_id, inv)
        log_location_draw(ctx.slot_id, location_card, inv.location_title)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {"location_card": location_card, "deck_size": len(inv.whispers_deck) + 1, **draw}


def draw_whisper_card(ctx: PlayContext, *, card: str | None = None) -> dict[str, Any]:
    inv = get_investigation(ctx)
    if not inv.deck_built:
        raise ValueError("Build the Whispers deck first.")
    if inv.is_ended():
        raise ValueError("Investigation has ended.")
    card_source, _, _ = get_play_settings(ctx)
    if card_source == "physical" and not card:
        raise ValueError("Physical deck mode: report the card you drew in chat.")
    if not inv.whispers_deck and not card:
        raise ValueError("Whispers deck is empty.")
    drawn = card or inv.whispers_deck.pop(0)
    if card_source == "physical":
        canonical = normalize_card_name(card or "")
        if not canonical:
            raise ValueError(f"Could not parse card: {card!r}")
        drawn = canonical
    is_final = not inv.whispers_deck
    draw = format_card_draw(
        drawn,
        jokers_drawn_before=inv.jokers_drawn,
        is_final_card=is_final,
    )
    inv.discard_pile.append(drawn)
    inv.turn_number += 1
    inv.last_card = drawn
    inv.last_table = str(draw.get("table") or "")
    inv.last_title = str(draw.get("title") or "")
    inv.last_prompt = str(draw.get("prompt") or "")
    if draw.get("is_joker"):
        inv.jokers_drawn += 1
        if draw.get("trigger_joker_ending"):
            inv.force_joker_ending = True
    if is_final or inv.force_joker_ending:
        inv.investigation_complete = True
    ctx.entity = investigation_to_dict(inv)
    save_investigation(inv)
    if ctx.slot_id:
        log_whisper_draw(ctx.slot_id, inv, drawn, inv.last_table)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {"card": drawn, "is_final": is_final, **draw}


def format_draw_message(inv: WhispersInvestigation, draw: dict[str, Any]) -> str:
    label = "Final draw" if draw.get("is_final") else "Whisper draw"
    user_message = f"**{label}:** {draw['card']}\n\n{draw.get('prompt', '')}"
    if draw.get("trigger_joker_ending") and draw.get("ending"):
        user_message += f"\n\n**Joker's Ending**\n\n{draw['ending']}"
    return user_message


def _journal_context(inv: WhispersInvestigation, draw: dict[str, Any]) -> str:
    return f"Prompt ({draw.get('table', '')}): {draw.get('prompt', '')[:2000]}\nCard: {draw.get('card', '')}"


def generate_ai_journal(
    ctx: PlayContext,
    inv: WhispersInvestigation,
    draw: dict[str, Any],
    *,
    chat_provider: ChatProvider,
) -> str | None:
    _, story_mode, _ = get_play_settings(ctx)
    if story_mode != "ai_narrator":
        return None
    try:
        story_so_far = narrative_context_for_ai(ctx.slot_id) if ctx.slot_id else ""
        prose = synthesize_journal_entry(
            _journal_context(inv, draw),
            investigator_name=inv.investigator_name,
            location_name=inv.location_name or inv.location_title,
            turn_number=inv.turn_number,
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


def build_draw_answer(
    ctx: PlayContext,
    inv: WhispersInvestigation,
    draw: dict[str, Any],
    *,
    chat_provider: ChatProvider,
) -> str:
    prose = generate_ai_journal(ctx, inv, draw, chat_provider=chat_provider)
    if prose:
        return prose
    return format_draw_message(inv, draw)


def perform_whisper_draw(
    ctx: PlayContext,
    *,
    chat_provider: ChatProvider,
    card: str | None = None,
) -> tuple[dict[str, Any], str, str]:
    draw = draw_whisper_card(ctx, card=card)
    inv = get_investigation(ctx)
    user_message = format_draw_message(inv, draw)
    answer = build_draw_answer(ctx, inv, draw, chat_provider=chat_provider)
    return draw, user_message, answer




def shortcuts_payload(ctx: PlayContext) -> list[dict]:
    inv = get_investigation(ctx)
    return [
        dict(s)
        for s in shortcuts_for_investigation(
            deck_built=inv.deck_built,
            investigation_complete=inv.investigation_complete,
            force_joker_ending=inv.force_joker_ending,
        )
    ]


def execute_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, str, list[dict], str]:
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    _ = prior_history or recent_chat_history(ctx.messages)
    return run_investigation_shortcut(
        ctx,
        shortcut_id,
        chat_provider=app.chat_provider,
        retrieval_cfg=retrieval_cfg,
        top_k=app.top_k,
        factions=app.selected_factions,
    )


def run_investigation_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in SHORTCUT_IDS:
        raise ValueError(f"Unknown Whispers shortcut: {shortcut_id}")

    route = f"whispers:{shortcut_id}"
    store = _store()

    if shortcut_id == "build_deck":
        draw = build_deck(ctx)
        inv = get_investigation(ctx)
        user_message = (
            f"**Whispers deck built** ({len(inv.whispers_deck) + 1} cards)\n\n"
            f"**Location draw:** {draw['location_card']}\n\n{draw.get('prompt', '')}"
        )
        answer = build_draw_answer(ctx, inv, draw, chat_provider=chat_provider)
        if store:
            store.persist_ctx(ctx)
        return user_message, answer, [], route

    if shortcut_id == "draw_whisper":
        _, user_message, answer = perform_whisper_draw(ctx, chat_provider=chat_provider)
        if store:
            store.persist_ctx(ctx)
        return user_message, answer, [], route

    run = run_shortcut(shortcut_id, **shortcut_kwargs(ctx))
    user_message = run["user_message"]

    if shortcut_id == "oracle" and run.get("dice") and ctx.slot_id and store:
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
    card_source, _, _ = get_play_settings(ctx)
    if card_source == "physical":
        card = normalize_card_name(prompt)
        if card and (is_joker_card(card) or " of " in card.lower()):
            inv = get_investigation(ctx)
            if inv.deck_built and not inv.is_ended():
                try:
                    _, user_message, answer = perform_whisper_draw(ctx, card=card, chat_provider=app.chat_provider)
                    messages = append_chat_exchange(app, ctx, user_message, answer)
                    store = _store()
                    if store:
                        store.persist_ctx(ctx)
                    return answer, messages, "whispers:physical_draw"
                except ValueError:
                    pass

    shortcut_id = match_whispers_shortcut(prompt)
    if not shortcut_id:
        return None
    user_message, answer, sources, route = execute_shortcut(
        ctx, shortcut_id, app=app, prior_history=prior_history
    )
    messages = append_chat_exchange(app, ctx, user_message, answer)
    app.last_sources = sources
    return answer, messages, route


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines)
