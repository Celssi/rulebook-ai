"""Brambletrek business logic for API (no Streamlit)."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history, to_langchain_history
GAME_ID = "brambletrek"
from src.games.brambletrek.actions import (
    match_brambletrek_shortcut,
    run_shortcut,
    shortcuts_for_character,
)
from src.games.brambletrek.character import (
    character_from_dict,
    character_to_dict,
    default_character,
    format_summary as format_character_summary,
    get_legacy_options,
    label_for_band,
    load_character_tables,
    save_character,
    table_options,
)
from src.games.brambletrek.curated import (
    adventure_options,
    apply_item_effects,
    apply_single_journey_event,
    event_needs_item_draw,
    format_item_draw,
    format_reason_ending,
    item_effect_preview,
    journey_depths_trace,
    legacy_abilities,
    lookup_item,
    lookup_journey_event,
    overcome_the_odds,
    reset_daily_legacy_abilities,
)
from src.games.brambletrek.lonelog import (
    card_short_label,
    format_mechanical,
    format_resources,
    log_draw,
    log_mechanical,
    log_narrative,
    log_player_action,
    open_scene,
    read_tail,
)
from src.games.brambletrek.narrator import synthesize_narrator_line
from src.games.brambletrek.roster import create_character, delete_character, list_characters, load_character
from src.games.saves import AppSession, PlayContext, get_play_store
from src.llm import ChatProvider
# rag_query is imported lazily at the call site (avoids src.rag <-> registry cycle).
from src.tools import draw_cards, format_card_result

PENDING_JOURNEY_KEY = "pending_journey"


def _store():
    return get_play_store(GAME_ID)


def get_character(ctx: PlayContext):
    return character_from_dict(ctx.entity or {})


def persist_character(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    old = get_character(ctx)
    char = character_from_dict(raw)
    char.clamp_stats()
    if ctx.slot_id:
        char.id = ctx.slot_id
    if char.legacy != old.legacy:
        from src.games.brambletrek.character import apply_legacy_stat_change, legacy_stat_deltas

        oh, om, os = legacy_stat_deltas(old.legacy)
        nh, nm, ns = legacy_stat_deltas(char.legacy)
        pre_applied = (
            char.health == max(0, min(20, old.health - oh + nh))
            and char.morale == max(0, min(20, old.morale - om + nm))
            and char.supplies == max(0, min(20, old.supplies - os + ns))
        )
        if pre_applied:
            char.legacy_abilities_used = {}
        else:
            apply_legacy_stat_change(char, old.legacy, char.legacy)
    ctx.entity = character_to_dict(char)
    save_character(char)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str]:
    store = _store()
    if not store:
        return "player", "virtual"
    settings = store.get_settings_ctx(ctx)
    return settings.get("story_mode", "player"), settings.get("card_source", "virtual")


def shortcut_kwargs(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    _, card_source = get_play_settings(ctx)
    return {
        "in_aldwund": char.in_aldwund,
        "reason_band": char.reason_band,
        "active_adventure": char.active_adventure,
        "legacy": char.legacy,
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
    }


def log_user_prompt(ctx: PlayContext, prompt: str) -> None:
    if not ctx.slot_id:
        return
    stripped = prompt.strip()
    char = get_character(ctx)
    if stripped.startswith("@"):
        log_player_action(ctx.slot_id, stripped, char=char)
    elif stripped.startswith("?"):
        from src.games.brambletrek.lonelog import log_oracle

        log_oracle(ctx.slot_id, stripped, char=char)


def journey_event_stat_preview(event: dict) -> str:
    parts: list[str] = []
    for key, icon in (("health", "Health"), ("morale", "Morale"), ("supplies", "Supplies")):
        val = event.get(key)
        if val is not None and val != 0:
            sign = "+" if int(val) > 0 else ""
            parts.append(f"{icon} {sign}{val}")
    if event.get("all_stats") is not None:
        v = int(event["all_stats"])
        sign = "+" if v > 0 else ""
        parts.append(f"All stats {sign}{v}")
    if event.get("combat"):
        parts.append("Combat")
    for tag in event.get("tags") or []:
        parts.append(f"({tag.upper()})")
    return ", ".join(parts) if parts else "—"


def stash_pending_journey(ctx: PlayContext, run: dict, shortcut_id: str) -> str:
    cards = run.get("journey_cards")
    if not cards or shortcut_id not in ("journey_day", "aldwund_day"):
        return ""
    char = get_character(ctx)
    ctx.set_extra(
        PENDING_JOURNEY_KEY,
        {
            "cards": cards,
            "applied": [False] * len(cards),
            "item_cards": [None] * len(cards),
            "depths_trace": journey_depths_trace(cards, start_in_aldwund=char.in_aldwund),
            "shortcut_id": shortcut_id,
        },
    )
    if ctx.slot_id:
        log_draw(ctx.slot_id, cards, label="Journey draw 4", char=char)
    return (
        "\n\n_Apply each event in the **Today's draws** panel when you resolve it "
        "(combat, abilities, and items happen between cards — not all at once)._"
    )


def _journey_item_cards(pending: dict, n_events: int) -> list[str | None]:
    cards = pending.get("item_cards")
    if not isinstance(cards, list) or len(cards) != n_events:
        cards = [None] * n_events
        pending["item_cards"] = cards
    return cards


def _draw_journey_item(char, ctx: PlayContext, event_index: int, pending: dict, *, event: dict | None):
    if not event_needs_item_draw(event):
        return None
    n_events = len(pending.get("cards") or [])
    item_cards = _journey_item_cards(pending, n_events)
    if event_index < len(item_cards) and item_cards[event_index]:
        return None
    ctx.sync_deck()
    result = draw_cards(count=1, game_id=GAME_ID, char_id=ctx.slot_id or None)
    ctx.refresh_deck()
    if not result.get("ok"):
        return result.get("error") or "Could not draw item card — deck may be empty."
    item_card = result["cards"][0]
    item_cards[event_index] = item_card
    pending["item_cards"] = item_cards
    item = lookup_item(item_card)
    effect_line = apply_item_effects(char, item) if item else ""
    if ctx.slot_id:
        log_draw(ctx.slot_id, [item_card], label="Item draw", char=char)
        log_mechanical(ctx.slot_id, format_item_draw(item_card), char=char)
        if effect_line and effect_line != "No immediate stat change":
            log_mechanical(ctx.slot_id, effect_line, char=char)
            log_mechanical(
                ctx.slot_id,
                format_resources(char.health, char.morale, char.supplies),
                char=char,
            )
    return None


def pending_journey_payload(ctx: PlayContext) -> dict | None:
    pending = ctx.get_extra(PENDING_JOURNEY_KEY)
    if not pending:
        return None
    char = get_character(ctx)
    cards = pending.get("cards") or []
    applied = list(pending.get("applied") or [False] * len(cards))
    trace = pending.get("depths_trace") or journey_depths_trace(
        cards, start_in_aldwund=bool(char.in_aldwund)
    )
    item_cards = _journey_item_cards(pending, len(cards))
    events = []
    for i, card in enumerate(cards):
        in_depths = trace[i] if i < len(trace) else char.in_aldwund
        event = lookup_journey_event(card, in_depths=in_depths)
        item_card = item_cards[i] if i < len(item_cards) else None
        item = lookup_item(item_card) if item_card else None
        events.append(
            {
                "index": i,
                "card": card,
                "zone": "Depths" if in_depths else "Surface",
                "applied": applied[i] if i < len(applied) else False,
                "can_apply": i == 0 or (i > 0 and applied[i - 1]),
                "label": event.get("label") if event else None,
                "preview": journey_event_stat_preview(event or {}),
                "needs_item": bool(event and event_needs_item_draw(event)),
                "item_card": item_card,
                "item_label": item.get("label") if item else None,
                "item_preview": item_effect_preview(item) if item else None,
            }
        )
    return {"events": events, "shortcut_id": pending.get("shortcut_id")}


def apply_journey_event(ctx: PlayContext, event_index: int) -> dict:
    pending = ctx.get_extra(PENDING_JOURNEY_KEY)
    if not pending:
        raise ValueError("No pending journey")
    cards = pending.get("cards") or []
    applied = list(pending.get("applied") or [False] * len(cards))
    trace = pending.get("depths_trace") or []
    if event_index < 0 or event_index >= len(cards):
        raise ValueError("Invalid event index")
    if applied[event_index]:
        raise ValueError("Event already applied")
    if event_index > 0 and not applied[event_index - 1]:
        raise ValueError("Apply previous events first")
    char = get_character(ctx)
    card = cards[event_index]
    in_depths = trace[event_index] if event_index < len(trace) else char.in_aldwund
    event = lookup_journey_event(card, in_depths=in_depths)
    summary = apply_single_journey_event(char, card, in_depths=in_depths)
    applied[event_index] = True
    pending["applied"] = applied
    item_error = _draw_journey_item(char, ctx, event_index, pending, event=event)
    ctx.set_extra(PENDING_JOURNEY_KEY, pending)
    persist_character(ctx, character_to_dict(char))
    if ctx.slot_id:
        preview = journey_event_stat_preview(event or {})
        log_mechanical(ctx.slot_id, f"{card_short_label(card)} {preview}", char=char)
        log_mechanical(
            ctx.slot_id,
            format_resources(char.health, char.morale, char.supplies),
            char=char,
        )
    return {
        "summary": summary,
        "item_error": item_error,
        "entity": ctx.entity,
        "header": character_header(ctx),
        "pending_journey": pending_journey_payload(ctx),
    }


def draw_journey_item(ctx: PlayContext, event_index: int) -> dict:
    pending = ctx.get_extra(PENDING_JOURNEY_KEY)
    if not pending:
        raise ValueError("No pending journey")
    char = get_character(ctx)
    cards = pending.get("cards") or []
    trace = pending.get("depths_trace") or []
    in_depths = trace[event_index] if event_index < len(trace) else char.in_aldwund
    event = lookup_journey_event(cards[event_index], in_depths=in_depths)
    item_error = _draw_journey_item(char, ctx, event_index, pending, event=event)
    ctx.set_extra(PENDING_JOURNEY_KEY, pending)
    persist_character(ctx, character_to_dict(char))
    return {
        "item_error": item_error,
        "entity": ctx.entity,
        "header": character_header(ctx),
        "pending_journey": pending_journey_payload(ctx),
    }


def finish_journey_day(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    char.journey_day = max(1, char.journey_day + 1)
    reset_daily_legacy_abilities(char)
    char.clamp_stats()
    persist_character(ctx, character_to_dict(char))
    if ctx.slot_id:
        open_scene(ctx.slot_id, char)
        log_mechanical(
            ctx.slot_id,
            format_resources(char.health, char.morale, char.supplies),
            char=char,
        )
    ctx.set_extra(PENDING_JOURNEY_KEY, None)
    return {"entity": ctx.entity, "header": character_header(ctx), "pending_journey": None}


def discard_journey(ctx: PlayContext) -> dict:
    ctx.set_extra(PENDING_JOURNEY_KEY, None)
    return {"pending_journey": None}


def bulk_apply_journey(ctx: PlayContext) -> dict:
    pending = ctx.get_extra(PENDING_JOURNEY_KEY)
    if not pending:
        raise ValueError("No pending journey")
    char = get_character(ctx)
    cards = pending.get("cards") or []
    applied = list(pending.get("applied") or [False] * len(cards))
    trace = pending.get("depths_trace") or []
    for i, card in enumerate(cards):
        if applied[i]:
            continue
        ev = lookup_journey_event(
            card, in_depths=trace[i] if i < len(trace) else char.in_aldwund
        )
        if ev and ev.get("combat"):
            continue
        apply_single_journey_event(
            char, card, in_depths=trace[i] if i < len(trace) else char.in_aldwund
        )
        applied[i] = True
        if ctx.slot_id:
            preview = journey_event_stat_preview(ev or {})
            log_mechanical(ctx.slot_id, f"{card_short_label(card)} {preview}", char=char)
    pending["applied"] = applied
    ctx.set_extra(PENDING_JOURNEY_KEY, pending)
    persist_character(ctx, character_to_dict(char))
    if ctx.slot_id:
        log_mechanical(
            ctx.slot_id,
            format_resources(char.health, char.morale, char.supplies),
            char=char,
        )
    return {"entity": ctx.entity, "header": character_header(ctx), "pending_journey": pending_journey_payload(ctx)}


def maybe_narrator_log(ctx: PlayContext, context: str, *, chat_provider: ChatProvider) -> str | None:
    story_mode, _ = get_play_settings(ctx)
    if story_mode != "ai_narrator" or not ctx.slot_id:
        return None
    try:
        prose = synthesize_narrator_line(context, chat_provider=chat_provider)
        if prose:
            log_narrative(ctx.slot_id, prose, char=get_character(ctx))
            return prose
    except Exception:
        pass
    return None


def answer_table_lookup_prompt(
    prompt: str,
    ctx: PlayContext,
    *,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider = "ollama",
) -> tuple[str, list[dict], str]:
    factions = selected_factions if selected_factions else None
    effective_top_k = max(top_k, 8)
    lower = prompt.lower()
    if "random gnawborn" in lower or "character creation" in lower:
        effective_top_k = max(effective_top_k, 12)
    if "adventure scene" in lower:
        effective_top_k = max(effective_top_k, 14)
    if "journey" in lower or "exploration" in lower or "event 1" in lower:
        effective_top_k = max(effective_top_k, 12)
    from src.rag import query as rag_query

    result = rag_query(
        prompt,
        top_k=effective_top_k,
        factions=factions,
        game_state=None,
        game_id=GAME_ID,
        chat_history=[],
        candidate_k=retrieval_cfg["candidate_k"],
        use_hybrid=retrieval_cfg["use_hybrid"],
        use_rerank=retrieval_cfg.get("use_rerank", False),
        play_entity=ctx.entity,
        chat_provider=chat_provider,
    )
    return result.answer, result.sources, "rag"


def execute_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, str, list[dict], str]:
    from src.retrieval_profiles import resolve_retrieval_profile

    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    top_k = app.top_k
    factions = app.selected_factions
    chat_provider = app.chat_provider
    history = prior_history or recent_chat_history(ctx.messages)

    run = run_shortcut(shortcut_id, game_id=GAME_ID, **shortcut_kwargs(ctx))
    kind = run["kind"]
    route = f"brambletrek:{shortcut_id}"
    user_message = run["user_message"]

    if kind == "static":
        return user_message, user_message, [], route

    if kind in {"multi_draw_rag", "rag_only", "roll_rag"}:
        answer, sources, _ = answer_table_lookup_prompt(
            run["prompt"],
            ctx,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=factions,
            chat_provider=chat_provider,
        )
        if kind in {"multi_draw_rag", "roll_rag"}:
            stat_note = stash_pending_journey(ctx, run, shortcut_id)
            answer = f"{run['user_message']}{stat_note}\n\n{answer}"
            narrator = maybe_narrator_log(ctx, answer, chat_provider=chat_provider)
            if narrator:
                answer = f"{answer}\n\n---\n\n{narrator}"
        ctx.refresh_deck()
        store = _store()
        if store:
            store.persist_ctx(ctx)
        return user_message, answer, sources, route

    from src.agent import run_agent

    out = run_agent(
        run["prompt"],
        history=to_langchain_history(history),
        game_state=None,
        game_id=GAME_ID,
        retrieval=retrieval_cfg,
        play_entity=ctx.entity,
        chat_provider=chat_provider,
        char_id=ctx.slot_id or None,
        story_mode=get_play_settings(ctx)[0],
        card_source=get_play_settings(ctx)[1],
    )
    ctx.refresh_deck()
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return user_message, out["answer"], out.get("sources", []), route


def try_handle_prompt(
    ctx: PlayContext,
    prompt: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]],
) -> tuple[str, list[dict], str] | None:
    stripped = prompt.strip().lower()
    if stripped in {"/day", "/journey"}:
        day_shortcut = (
            "adventure_scene" if (get_character(ctx).active_adventure or "") else "journey_day"
        )
        return execute_shortcut(ctx, day_shortcut, app=app, prior_history=prior_history)[1:]
    shortcut_id = match_brambletrek_shortcut(
        prompt,
        active_adventure=get_character(ctx).active_adventure or "",
    )
    if shortcut_id:
        return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]
    return None


def character_options_payload() -> dict:
    from src.games.brambletrek.curated import _legacies_data

    legacies = []
    for lid, data in get_legacy_options().items():
        if not lid:
            continue
        raw = (_legacies_data().get("legacies") or {}).get(lid) or {}
        legacies.append(
            {
                "id": lid,
                "label": data["label"],
                "boost": data.get("boost"),
                "flaw": data.get("flaw"),
                "health_delta": int(raw.get("health_delta", 0) or 0),
                "morale_delta": int(raw.get("morale_delta", 0) or 0),
                "supplies_delta": int(raw.get("supplies_delta", 0) or 0),
                "abilities": [
                    {
                        "id": ab["id"],
                        "label": ab["label"],
                        "description": ab.get("description", ""),
                        "tags": ab.get("tags") or [],
                    }
                    for ab in legacy_abilities(lid)
                ],
            }
        )
    return {
        "reasons": [{"id": o[0], "label": o[1]} for o in table_options("reasons")],
        "backgrounds": [{"id": o[0], "label": o[1]} for o in table_options("backgrounds")],
        "trinkets": [{"id": o[0], "label": o[1]} for o in table_options("trinkets")],
        "card_bands": [
            {"id": str(row.get("id", "")), "label": str(row.get("label", ""))}
            for row in (load_character_tables().get("card_bands") or [])
            if isinstance(row, dict) and row.get("id")
        ],
        "legacies": legacies,
        "adventures": [{"id": o[0], "label": o[1]} for o in adventure_options()],
    }


def legacy_abilities_payload(legacy_id: str, used_map: dict[str, bool]) -> list[dict]:
    abilities = []
    for ab in legacy_abilities(legacy_id):
        abilities.append(
            {
                "id": ab["id"],
                "label": ab["label"],
                "description": ab.get("description", ""),
                "tags": ab.get("tags") or [],
                "used": used_map.get(ab["id"], False),
            }
        )
    oto = overcome_the_odds()
    abilities.append(
        {
            "id": oto["id"],
            "label": oto["label"],
            "description": oto.get("description", ""),
            "tags": ["universal"],
            "used": used_map.get(oto["id"], False),
        }
    )
    return abilities


def shortcuts_payload(ctx: PlayContext) -> list[dict]:
    char = get_character(ctx)
    return [
        {"id": s["id"], "label": s["label"]}
        for s in shortcuts_for_character(active_adventure=char.active_adventure or "")
    ]


def roster_payload() -> list[dict]:
    entries: list[dict] = []
    for entry in list_characters():
        char = load_character(entry.id)
        name = char.name.strip() if hasattr(char, "name") else str(char.get("name", "") or "").strip()
        entries.append({"id": entry.id, "name": name})
    return entries


def create_gnawborn(name: str) -> dict:
    char = create_character(name)
    return character_to_dict(char)


def delete_gnawborn(char_id: str) -> None:
    delete_character(char_id)


def switch_gnawborn(app: AppSession, char_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Brambletrek store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, char_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_character(ctx: PlayContext) -> dict:
    reset = default_character()
    if ctx.slot_id:
        reset.id = ctx.slot_id
    return persist_character(ctx, character_to_dict(reset))


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines=n_lines)


def reason_ending_preview(reason_band: str) -> str:
    return format_reason_ending(
        reason_band,
        reason_label=label_for_band("reasons", reason_band) if reason_band else "",
    )


_CHARACTER_TABLES = {
    "reason": ("reasons", "reason_band", "reason_card"),
    "background": ("backgrounds", "background_band", "background_card"),
    "trinket": ("trinkets", "trinket_band", "trinket_card"),
}


def draw_character_table(ctx: PlayContext, table: str) -> dict:
    meta = _CHARACTER_TABLES.get(table)
    if not meta:
        raise ValueError(f"Unknown table: {table}")
    table_key, _, _ = meta
    from src.games.brambletrek.character import character_table_band
    from src.games.brambletrek.curated import parse_playing_card

    result = draw_cards(count=1, game_id=GAME_ID, char_id=ctx.slot_id or None)
    if not result.get("ok"):
        raise ValueError(result.get("error") or result.get("summary") or "Deck draw failed")
    card = result["cards"][0]
    parsed = parse_playing_card(card)
    if not parsed:
        raise ValueError(f"Could not parse drawn card: {card}")
    band_id = character_table_band(parsed["rank_key"])
    store = _store()
    if ctx.slot_id and store:
        log_draw(
            ctx.slot_id,
            [card],
            label=f"{table.title()} table draw",
            char=get_character(ctx),
        )
        ctx.refresh_deck()
        store.persist_ctx(ctx)
    return {
        "table": table,
        "band_id": band_id,
        "band_field": meta[1],
        "card_field": meta[2],
        "card": card,
        "row_label": label_for_band(table_key, band_id),
        "remaining": result.get("remaining", 0),
    }


def character_header(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    return {
        "summary": format_character_summary(char),
        "health": char.health,
        "morale": char.morale,
        "supplies": char.supplies,
        "journey_day": char.journey_day,
        "name": char.name,
        "legacy": char.legacy,
        "legacy_label": get_legacy_options().get(char.legacy, {}).get("label", ""),
        "in_aldwund": char.in_aldwund,
    }
