"""Brambletrek 2 business logic for API."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history, to_langchain_history
from src.games.brambletrek_2.actions import (
    match_brambletrek_2_shortcut,
    run_shortcut,
    shortcuts_for_character,
)
from src.games.brambletrek_2.character import (
    Brambletrek2Character,
    arrival_band,
    character_from_dict,
    character_to_dict,
    default_character,
    format_summary as format_character_summary,
    get_legacy_options,
    save_character,
)
from src.games.brambletrek_2.curated import (
    apply_event_deltas,
    apply_single_exploration_event,
    event_needs_item_draw,
    event_triggers_hollow,
    format_arrival_draw,
    format_exploration_events,
    format_hollow_event,
    format_item_draw,
    format_overcome_odds,
    legacy_abilities,
    lookup_arrival,
    lookup_exploration_event,
    lookup_hollow_event,
    lookup_item,
    overcome_the_odds,
    parse_playing_card,
    reset_daily_legacy_abilities,
)
from src.games.brambletrek_2.hollow import (
    adjacent_unrevealed,
    all_revealed,
    new_hollow_grid,
    reveal_cell,
    reshuffle_face_down,
)
from src.games.brambletrek_2.lonelog import (
    card_short_label,
    format_resources,
    log_draw,
    log_mechanical,
    log_narrative,
    log_player_action,
    open_scene,
    read_tail,
)
from src.games.brambletrek_2.narrator import synthesize_narrator_line
from src.games.brambletrek_2.roster import create_character, delete_character, list_characters, load_character
from src.games.saves import AppSession, PlayContext, get_play_store
from src.rag import query as rag_query
from src.tools import draw_cards

GAME_ID = "brambletrek_2"
PENDING_EXPLORATION_KEY = "pending_exploration"


def _store():
    return get_play_store(GAME_ID)


def get_character(ctx: PlayContext) -> Brambletrek2Character:
    return character_from_dict(ctx.entity or {})


def persist_character(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    old = get_character(ctx)
    char = character_from_dict(raw)
    if char.legacy and char.legacy != old.legacy and char.health == old.health:
        char.apply_legacy_stats()
        char.legacy_abilities_used = {}
    char.clamp_stats()
    if ctx.slot_id:
        char.id = ctx.slot_id
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
        "legacy": char.legacy,
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
        "in_hollow": char.in_hollow,
    }


def log_user_prompt(ctx: PlayContext, prompt: str) -> None:
    if not ctx.slot_id:
        return
    stripped = prompt.strip()
    char = get_character(ctx)
    if stripped.startswith("@"):
        log_player_action(ctx.slot_id, stripped, char=char)
    elif stripped.startswith("?"):
        from src.games.brambletrek_2.lonelog import log_oracle

        log_oracle(ctx.slot_id, stripped, char=char)


def exploration_event_preview(event: dict) -> str:
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


def stash_pending_exploration(ctx: PlayContext, run: dict, shortcut_id: str) -> str:
    cards = run.get("exploration_cards")
    if not cards or shortcut_id != "exploration_day":
        return ""
    char = get_character(ctx)
    ctx.set_extra(
        PENDING_EXPLORATION_KEY,
        {
            "cards": cards,
            "applied": [False] * len(cards),
            "item_cards": [None] * len(cards),
        },
    )
    if ctx.slot_id:
        log_draw(ctx.slot_id, cards, label="Exploration draw 4", char=char)
    return (
        "\n\n_Apply each event in the **Exploration** panel when you resolve it "
        "(combat, hollow, and items happen between cards)._"
    )


def pending_exploration_payload(ctx: PlayContext) -> dict | None:
    pending = ctx.get_extra(PENDING_EXPLORATION_KEY)
    if not pending:
        return None
    cards = pending.get("cards") or []
    applied = list(pending.get("applied") or [False] * len(cards))
    item_cards = pending.get("item_cards") or [None] * len(cards)
    events = []
    for i, card in enumerate(cards):
        event = lookup_exploration_event(card)
        item_card = item_cards[i] if i < len(item_cards) else None
        item = lookup_item(item_card) if item_card else None
        events.append(
            {
                "index": i,
                "card": card,
                "applied": applied[i] if i < len(applied) else False,
                "can_apply": i == 0 or (i > 0 and applied[i - 1]),
                "label": event.get("label") if event else None,
                "preview": exploration_event_preview(event or {}),
                "needs_item": bool(event and event_needs_item_draw(event)),
                "needs_hollow": bool(event and event_triggers_hollow(event)),
                "item_card": item_card,
                "item_label": item.get("label") if item else None,
            }
        )
    return {"events": events}


def apply_exploration_event(ctx: PlayContext, event_index: int) -> dict:
    pending = ctx.get_extra(PENDING_EXPLORATION_KEY)
    if not pending:
        raise ValueError("No pending exploration")
    cards = pending.get("cards") or []
    applied = list(pending.get("applied") or [False] * len(cards))
    if event_index < 0 or event_index >= len(cards):
        raise ValueError("Invalid event index")
    if applied[event_index]:
        raise ValueError("Event already applied")
    if event_index > 0 and not applied[event_index - 1]:
        raise ValueError("Apply previous events first")
    char = get_character(ctx)
    card = cards[event_index]
    event = lookup_exploration_event(card)
    summary = apply_single_exploration_event(char, card)
    applied[event_index] = True
    pending["applied"] = applied
    if event and event_needs_item_draw(event):
        ctx.sync_deck()
        result = draw_cards(count=1, game_id=GAME_ID, char_id=ctx.slot_id or None)
        ctx.refresh_deck()
        if result.get("ok"):
            item_card = result["cards"][0]
            item_cards = list(pending.get("item_cards") or [None] * len(cards))
            item_cards[event_index] = item_card
            pending["item_cards"] = item_cards
            item = lookup_item(item_card)
            if item:
                apply_event_deltas(char, item)
            if ctx.slot_id:
                log_draw(ctx.slot_id, [item_card], label="Item draw", char=char)
                log_mechanical(ctx.slot_id, format_item_draw(item_card), char=char)
    ctx.set_extra(PENDING_EXPLORATION_KEY, pending)
    persist_character(ctx, character_to_dict(char))
    if ctx.slot_id:
        log_mechanical(
            ctx.slot_id,
            f"{card_short_label(card)} {exploration_event_preview(event or {})}",
            char=char,
        )
        log_mechanical(
            ctx.slot_id,
            format_resources(char.health, char.morale, char.supplies),
            char=char,
        )
    return {
        "summary": summary,
        "entity": ctx.entity,
        "header": character_header(ctx),
        "pending_exploration": pending_exploration_payload(ctx),
    }


def finish_exploration_day(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    char.exploration_day = max(1, char.exploration_day + 1)
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
    ctx.set_extra(PENDING_EXPLORATION_KEY, None)
    return {
        "entity": ctx.entity,
        "header": character_header(ctx),
        "pending_exploration": None,
    }


def discard_exploration(ctx: PlayContext) -> dict:
    ctx.set_extra(PENDING_EXPLORATION_KEY, None)
    return {"pending_exploration": None}


def enter_hollow(ctx: PlayContext, run: dict) -> None:
    char = get_character(ctx)
    entry_card = run.get("hollow_entry_card", "")
    grid_cards = run.get("hollow_grid_cards") or []
    entry_prompt = run.get("hollow_entry_prompt", "")
    char.in_hollow = True
    char.hollow_state = new_hollow_grid(
        grid_cards, entry_card=entry_card, entry_prompt=entry_prompt
    )
    if char.hollow_state and char.hollow_state.grid:
        reveal_cell(char.hollow_state, 0, 0)
    persist_character(ctx, character_to_dict(char))


def hollow_move(ctx: PlayContext, row: int, col: int) -> dict:
    char = get_character(ctx)
    if not char.in_hollow or not char.hollow_state:
        raise ValueError("Not in the Hollow")
    adj = adjacent_unrevealed(char.hollow_state)
    if (row, col) not in adj:
        raise ValueError("Invalid hollow move")
    cell = reveal_cell(char.hollow_state, row, col)
    if not cell or not cell.card:
        raise ValueError("No card at cell")
    event = lookup_hollow_event(cell.card)
    summary = format_hollow_event(cell.card)
    if event:
        apply_event_deltas(char, event)
        if event.get("suit") == "clubs":
            char.hollow_clubs_seen += 1
            if char.hollow_clubs_seen >= 5:
                ctx.sync_deck()
                result = draw_cards(count=20, game_id=GAME_ID, char_id=ctx.slot_id or None)
                ctx.refresh_deck()
                if result.get("ok"):
                    reshuffle_face_down(char.hollow_state, result["cards"])
                char.hollow_clubs_seen = 0
        if all_revealed(char.hollow_state):
            char.in_hollow = False
            char.hollow_state = None
            char.memory_fragments = 0
            char.hollow_awareness = False
            summary += "\n\n_All cards revealed — you leave the Hollow freely._"
    persist_character(ctx, character_to_dict(char))
    if ctx.slot_id:
        log_mechanical(ctx.slot_id, f"@ Hollow {row},{col}: {summary}", char=char)
    return {
        "summary": summary,
        "entity": ctx.entity,
        "header": character_header(ctx),
        "hollow": hollow_payload(ctx),
    }


def hollow_escape(ctx: PlayContext, run: dict) -> dict:
    char = get_character(ctx)
    if not char.hollow_awareness:
        raise ValueError("Need 3 memory fragments (awareness) before escape")
    cards = run.get("escape_cards") or []
    summary_parts = []
    if cards:
        from src.games.brambletrek_2.curated import lookup_hollow_exit, parse_playing_card

        anchor = parse_playing_card(cards[0])
        if anchor and anchor["suit"] in ("spades", "clubs"):
            char.health = max(0, char.health - 5)
            summary_parts.append("Hollow clings — lose 5 Health.")
        else:
            summary_parts.append("Hollow releases you peacefully.")
        if len(cards) > 1:
            exit_row = lookup_hollow_exit(cards[1])
            if exit_row:
                summary_parts.append(f"Exit: {exit_row.get('label', '')}")
    char.in_hollow = False
    char.hollow_state = None
    char.memory_fragments = 0
    char.hollow_awareness = False
    char.hollow_clubs_seen = 0
    persist_character(ctx, character_to_dict(char))
    summary = "\n".join(summary_parts) or "Escaped the Hollow."
    if ctx.slot_id:
        log_mechanical(ctx.slot_id, f"@ Escaped Hollow: {summary}", char=char)
    return {"summary": summary, "entity": ctx.entity, "header": character_header(ctx)}


def hollow_payload(ctx: PlayContext) -> dict | None:
    char = get_character(ctx)
    if not char.in_hollow or not char.hollow_state:
        return None
    st = char.hollow_state
    grid = []
    for r, row in enumerate(st.grid):
        grid.append(
            [
                {
                    "card": c.card,
                    "revealed": c.revealed,
                    "row": r,
                    "col": col,
                }
                for col, c in enumerate(row)
            ]
        )
    return {
        "entry_card": st.entry_card,
        "entry_prompt": st.entry_prompt,
        "grid": grid,
        "marker_row": st.marker_row,
        "marker_col": st.marker_col,
        "memory_fragments": char.memory_fragments,
        "awareness": char.hollow_awareness,
        "adjacent": [{"row": r, "col": c} for r, c in adjacent_unrevealed(st)],
    }


def maybe_narrator_log(ctx: PlayContext, answer: str, *, chat_provider: str) -> str:
    story_mode, _ = get_play_settings(ctx)
    if story_mode != "ai_narrator" or not ctx.slot_id:
        return ""
    line = synthesize_narrator_line(answer, chat_provider=chat_provider)
    if line:
        log_narrative(ctx.slot_id, line, char=get_character(ctx))
    return line


def answer_table_lookup_prompt(
    prompt: str,
    ctx: PlayContext,
    *,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str],
    chat_provider: str,
) -> tuple[str, list[dict], str]:
    result = rag_query(
        prompt,
        top_k=top_k,
        factions=selected_factions,
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
    hollow_row: int | None = None,
    hollow_col: int | None = None,
) -> tuple[str, str, list[dict], str]:
    from src.retrieval_profiles import resolve_retrieval_profile

    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    history = prior_history or recent_chat_history(ctx.messages)
    kw = shortcut_kwargs(ctx)
    kw["hollow_row"] = hollow_row
    kw["hollow_col"] = hollow_col
    run = run_shortcut(shortcut_id, game_id=GAME_ID, **kw)
    kind = run["kind"]
    route = f"brambletrek_2:{shortcut_id}"
    user_message = run["user_message"]

    if kind == "static":
        return user_message, user_message, [], route

    if shortcut_id == "hollow_enter" and kind == "multi_draw":
        enter_hollow(ctx, run)
        ctx.refresh_deck()
        store = _store()
        if store:
            store.persist_ctx(ctx)
        answer = user_message
        return user_message, answer, [], route

    if shortcut_id == "hollow_escape_attempt" and kind == "multi_draw":
        try:
            result = hollow_escape(ctx, run)
            answer = f"{user_message}\n\n{result['summary']}"
        except ValueError as e:
            answer = f"{user_message}\n\n_{e}_"
        ctx.refresh_deck()
        store = _store()
        if store:
            store.persist_ctx(ctx)
        return user_message, answer, [], route

    if kind in {"multi_draw_rag", "rag_only", "roll_rag", "card_rag"}:
        answer, sources, _ = answer_table_lookup_prompt(
            run["prompt"],
            ctx,
            retrieval_cfg=retrieval_cfg,
            top_k=app.top_k,
            selected_factions=app.selected_factions,
            chat_provider=app.chat_provider,
        )
        if kind == "multi_draw_rag":
            stat_note = stash_pending_exploration(ctx, run, shortcut_id)
            answer = f"{run['user_message']}{stat_note}\n\n{answer}"
            narrator = maybe_narrator_log(ctx, answer, chat_provider=app.chat_provider)
            if narrator:
                answer = f"{answer}\n\n---\n\n{narrator}"
        elif kind == "card_rag" and shortcut_id == "how_did_i_get_here":
            char = get_character(ctx)
            card = run.get("arrival_card", "")
            parsed = parse_playing_card(card) if card else None
            if parsed:
                arrival = lookup_arrival(card)
                char.how_did_i_get_here_card = card
                char.how_did_i_get_here = (
                    str(arrival.get("label", "")) if arrival else arrival_band(parsed["rank_key"])
                )
                persist_character(ctx, character_to_dict(char))
            answer = run["user_message"]
            sources = []
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
        chat_provider=app.chat_provider,
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
    if stripped in {"/day", "/exploration"}:
        return execute_shortcut(ctx, "exploration_day", app=app, prior_history=prior_history)[1:]
    shortcut_id = match_brambletrek_2_shortcut(prompt)
    if shortcut_id:
        return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]
    return None


def character_options_payload() -> dict:
    legacies = []
    for lid, data in get_legacy_options().items():
        if not lid:
            continue
        from src.games.brambletrek_2.curated import legacy_meta

        raw = legacy_meta(lid)
        legacies.append(
            {
                "id": lid,
                "label": data["label"],
                "tagline": data.get("tagline", ""),
                "health": int(raw.get("health", 10)),
                "morale": int(raw.get("morale", 10)),
                "supplies": int(raw.get("supplies", 10)),
                "abilities": [
                    {
                        "id": ab["id"],
                        "label": ab["label"],
                        "description": ab.get("description", ""),
                    }
                    for ab in legacy_abilities(lid)
                ],
            }
        )
    return {"legacies": legacies}


def legacy_abilities_payload(legacy_id: str, used_map: dict[str, bool]) -> list[dict]:
    abilities = []
    for ab in legacy_abilities(legacy_id):
        abilities.append(
            {
                "id": ab["id"],
                "label": ab["label"],
                "description": ab.get("description", ""),
                "used": used_map.get(ab["id"], False),
            }
        )
    oto = overcome_the_odds()
    abilities.append(
        {
            "id": oto["id"],
            "label": oto["label"],
            "description": oto.get("description", ""),
            "used": used_map.get(oto["id"], False),
        }
    )
    return abilities


def shortcuts_payload(ctx: PlayContext) -> list[dict]:
    return [{"id": s["id"], "label": s["label"]} for s in shortcuts_for_character()]


def roster_payload() -> list[dict]:
    entries: list[dict] = []
    for entry in list_characters():
        char = load_character(entry.id)
        name = char.name.strip() if hasattr(char, "name") else ""
        entries.append({"id": entry.id, "name": name})
    return entries


def create_traveller(name: str) -> dict:
    char = create_character(name)
    return character_to_dict(char)


def delete_traveller(char_id: str) -> None:
    delete_character(char_id)


def switch_traveller(app: AppSession, char_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Brambletrek 2 store unavailable")
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


def draw_arrival(ctx: PlayContext) -> dict:
    _, card_source = get_play_settings(ctx)
    if card_source == "physical":
        raise ValueError("Physical deck — draw a card and enter it manually in Settings.")
    ctx.sync_deck()
    result = draw_cards(count=1, game_id=GAME_ID, char_id=ctx.slot_id or None)
    ctx.refresh_deck()
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Deck draw failed")
    card = result["cards"][0]
    parsed = parse_playing_card(card)
    char = get_character(ctx)
    if parsed:
        arrival = lookup_arrival(card)
        char.how_did_i_get_here_card = card
        char.how_did_i_get_here = (
            str(arrival.get("label", "")) if arrival else arrival_band(parsed["rank_key"])
        )
        persist_character(ctx, character_to_dict(char))
    return {
        "card": card,
        "label": format_arrival_draw(card),
        "band": arrival_band(parsed["rank_key"]) if parsed else "",
        "entity": ctx.entity,
    }


def character_header(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    return {
        "summary": format_character_summary(char),
        "health": char.health,
        "morale": char.morale,
        "supplies": char.supplies,
        "exploration_day": char.exploration_day,
        "name": char.name,
        "legacy": char.legacy,
        "legacy_label": get_legacy_options().get(char.legacy, {}).get("label", ""),
        "in_hollow": char.in_hollow,
        "memory_fragments": char.memory_fragments,
        "hollow_awareness": char.hollow_awareness,
    }
