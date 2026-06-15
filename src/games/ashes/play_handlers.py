"""Play handlers (domain layer)."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history
from src.retrieval_profiles import resolve_retrieval_profile
GAME_ID = "ashes"
from src.games.ashes.actions import (
    SHORTCUT_IDS,
    match_ashes_shortcut,
    run_shortcut,
    shortcuts_for_scion,
)
from src.games.ashes.curated import class_options, ember_for_level, format_character_gift_draw, prompt_set_options
from src.games.ashes.lonelog import (
    log_journal,
    log_narrative,
    log_player_action,
    log_roll,
    log_room,
    narrative_context_for_ai,
    read_tail,
)
from src.games.ashes.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.ashes.roster import create_scion, delete_scion, list_scions, load_scion, save_scion
from src.games.ashes.scion import (
    AshesScion,
    format_summary,
    scion_from_dict,
    scion_to_dict,
)
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.llm import ChatProvider
# rag_query is imported lazily at the call site (avoids src.rag <-> registry cycle).
from src.tools import draw_cards


def _store():
    return get_play_store(GAME_ID)


def get_scion(ctx: PlayContext) -> AshesScion:
    return scion_from_dict(ctx.entity or {})


def persist_scion(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    scion = scion_from_dict(raw)
    scion.clamp()
    if ctx.slot_id:
        scion.id = ctx.slot_id
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str, str]:
    store = _store()
    if not store:
        return "virtual", "player", "crypt"
    settings = store.get_settings_ctx(ctx)
    card_source = settings.get("card_source", "virtual")
    story_mode = settings.get("story_mode", "player")
    prompt_set = settings.get("prompt_set", "crypt")
    return card_source, story_mode, prompt_set


def shortcut_kwargs(ctx: PlayContext) -> dict:
    card_source, _, prompt_set = get_play_settings(ctx)
    scion = get_scion(ctx)
    return {
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
        "prompt_set": prompt_set,
        "level": scion.level,
    }


def log_user_prompt(ctx: PlayContext, prompt: str) -> None:
    if not ctx.slot_id:
        return
    stripped = prompt.strip()
    if stripped.startswith("@"):
        log_player_action(ctx.slot_id, stripped)


def scion_header(ctx: PlayContext) -> dict:
    scion = get_scion(ctx)
    return {
        "summary": format_summary(scion),
        "name": scion.name,
        "scion_class": scion.scion_class,
        "pwr": scion.pwr,
        "int": scion.int_,
        "agl": scion.agl,
        "hp": scion.hp,
        "max_hp": scion.max_hp,
        "stamina": scion.stamina,
        "max_stamina": scion.max_stamina,
        "level": scion.level,
        "ember": scion.ember,
        "ember_to_level": ember_for_level(scion.level),
        "rooms_cleared": scion.rooms_cleared,
        "lore_count": scion.lore_count,
        "sanctuaries_visited": scion.sanctuaries_visited,
        "trials_completed": scion.trials_completed,
        "active_trials": list(scion.active_trials),
        "fate_gift": scion.fate_gift,
        "armour": scion.armour,
        "starting_weapon_melee": scion.starting_weapon_melee,
        "starting_weapon_ranged": scion.starting_weapon_ranged,
        "last_room_name": scion.last_room_name,
        "last_enemy": scion.last_enemy,
    }


def scion_options_payload() -> dict:
    return {"classes": class_options(), "prompt_sets": prompt_set_options()}


def roster_payload() -> list[dict]:
    entries: list[dict] = []
    for entry in list_scions():
        scion = load_scion(entry.id)
        name = scion.name.strip() if hasattr(scion, "name") else str(scion.get("name", "") or "").strip()
        entries.append({"id": entry.id, "name": name})
    return entries


def create_scion_entry(name: str) -> dict:
    scion = create_scion(name)
    return scion_to_dict(scion) if hasattr(scion, "id") else dict(scion)


def delete_scion_entry(scion_id: str) -> None:
    delete_scion(scion_id)


def switch_scion(app: AppSession, scion_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Ashes store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, scion_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_scion(ctx: PlayContext) -> dict:
    scion = AshesScion(id=ctx.slot_id or "")
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)
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
    scion = get_scion(ctx)
    card_source, _, _ = get_play_settings(ctx)
    from src.rag import query as rag_query

    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions or None,
        game_id=GAME_ID,
        play_entity=scion_to_dict(scion),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    _ = card_source
    return result.answer, result.sources


def _persist_room_draw(ctx: PlayContext, card: str, room: dict[str, Any]) -> None:
    scion = get_scion(ctx)
    scion.last_room_card = card
    scion.last_room_name = str(room.get("room") or "")
    scion.last_room_check = str(room.get("check") or "")
    scion.last_suit_feature = str(room.get("suit_feature") or "")
    scion.rooms_cleared += 1
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)
    if ctx.slot_id:
        log_room(ctx.slot_id, scion, card, scion.last_room_name, scion.last_room_check)


def _persist_journal_draw(ctx: PlayContext, card: str, journal: dict[str, Any]) -> None:
    scion = get_scion(ctx)
    scion.last_journal_card = card
    scion.last_journal_prompt = str(journal.get("event") or "")
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)
    if ctx.slot_id:
        log_journal(ctx.slot_id, card, scion.last_journal_prompt)


def _persist_trials_replace(ctx: PlayContext, run: dict[str, Any]) -> None:
    scion = get_scion(ctx)
    dr = run.get("draw_result") or {}
    trials = dr.get("trials") or []
    scion.active_trials = [
        {"card": str(t.get("card") or ""), "color": str(t.get("color") or ""), "trial": str(t.get("trial") or "")}
        for t in trials
    ]
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)


def _persist_trial_append(ctx: PlayContext, run: dict[str, Any]) -> None:
    scion = get_scion(ctx)
    dr = run.get("draw_result") or {}
    if len(scion.active_trials) >= 10:
        return
    scion.active_trials.append(
        {
            "card": str(dr.get("card") or (run.get("cards") or [""])[0]),
            "color": str(dr.get("color") or ""),
            "trial": str(dr.get("trial") or ""),
        }
    )
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)


def _maybe_ai_prose(
    ctx: PlayContext,
    scion: AshesScion,
    mechanics: str,
    *,
    chat_provider: ChatProvider,
) -> str | None:
    _, story_mode, _ = get_play_settings(ctx)
    if story_mode != "ai_narrator":
        return None
    try:
        story_so_far = narrative_context_for_ai(ctx.slot_id) if ctx.slot_id else ""
        prose = synthesize_journal_entry(
            mechanics,
            scion_name=scion.name,
            scion_class=scion.scion_class,
            rooms_cleared=scion.rooms_cleared,
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
        return prose
    except Exception:
        return None


def _persist_character_setup(ctx: PlayContext, run: dict[str, Any]) -> None:
    scion = get_scion(ctx)
    dr = run.get("draw_result") or {}
    gift = dr.get("gift") or {}
    if gift.get("gift"):
        scion.fate_gift = str(gift["gift"])
        cards = run.get("cards") or []
        if cards:
            scion.fate_gift_card = cards[0]
    armour = dr.get("armour")
    if armour:
        scion.armour = str(armour)
    if dr.get("armour_roll"):
        scion.armour_roll = int(dr["armour_roll"])
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)




def shortcuts_payload(ctx: PlayContext) -> list[dict]:
    _ = ctx
    return [dict(s) for s in shortcuts_for_scion()]


def run_scion_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in SHORTCUT_IDS:
        raise ValueError(f"Unknown Ashes shortcut: {shortcut_id}")

    route = f"ashes:{shortcut_id}"
    store = _store()
    _, story_mode, _ = get_play_settings(ctx)
    combat_room = False
    scion = get_scion(ctx)

    deck_shortcuts = (
        "draw_room",
        "draw_journal",
        "draw_room_journal",
        "draw_enemy",
        "character_gift",
        "character_setup",
        "draw_starting_trials",
        "draw_trial",
    )
    if shortcut_id in deck_shortcuts:
        ctx.sync_deck()

    run = run_shortcut(
        shortcut_id,
        **shortcut_kwargs(ctx),
        combat_room=combat_room,
    )
    user_message = run["user_message"]
    sources: list[dict] = []

    if shortcut_id == "draw_room" and run.get("cards"):
        _persist_room_draw(ctx, run["cards"][0], run.get("draw_result") or {})

    if shortcut_id == "draw_journal" and run.get("cards"):
        _persist_journal_draw(ctx, run["cards"][0], run.get("draw_result") or {})

    if shortcut_id == "draw_room_journal" and run.get("cards"):
        cards = run["cards"]
        dr = run.get("draw_result") or {}
        if dr.get("room"):
            _persist_room_draw(ctx, cards[0], dr["room"])
        if dr.get("journal"):
            _persist_journal_draw(ctx, cards[1], dr["journal"])

    if shortcut_id == "draw_enemy" and run.get("cards"):
        scion = get_scion(ctx)
        enemy = run.get("draw_result") or {}
        scion.last_enemy_card = run["cards"][0]
        scion.last_enemy = str(enemy.get("enemy") or "")
        ctx.entity = scion_to_dict(scion)
        save_scion(scion)

    if shortcut_id == "draw_starting_trials" and run.get("replace_trials"):
        _persist_trials_replace(ctx, run)

    if shortcut_id == "draw_trial" and run.get("append_trial"):
        _persist_trial_append(ctx, run)

    if shortcut_id in ("character_gift", "character_setup"):
        if shortcut_id == "character_gift" and run.get("cards"):
            scion = get_scion(ctx)
            gift = run.get("draw_result") or {}
            scion.fate_gift = str(gift.get("gift") or "")
            scion.fate_gift_card = run["cards"][0]
            ctx.entity = scion_to_dict(scion)
            save_scion(scion)
        if shortcut_id == "character_setup":
            _persist_character_setup(ctx, run)

    if shortcut_id == "character_armour" and run.get("armour_roll"):
        scion = get_scion(ctx)
        scion.armour_roll = int(run["armour_roll"])
        armour = lookup_armour_from_run(run)
        if armour:
            scion.armour = armour
        ctx.entity = scion_to_dict(scion)
        save_scion(scion)

    if shortcut_id == "roll_melee_weapon" and run.get("weapon"):
        scion = get_scion(ctx)
        scion.starting_weapon_melee = str(run["weapon"])
        ctx.entity = scion_to_dict(scion)
        save_scion(scion)

    if shortcut_id == "roll_ranged_weapon" and run.get("weapon"):
        scion = get_scion(ctx)
        scion.starting_weapon_ranged = str(run["weapon"])
        ctx.entity = scion_to_dict(scion)
        save_scion(scion)

    if shortcut_id == "sanctuary_check" and run.get("is_sanctuary"):
        scion = get_scion(ctx)
        scion.sanctuaries_visited += 1
        ctx.entity = scion_to_dict(scion)
        save_scion(scion)

    if run.get("dice") and ctx.slot_id and store:
        store.log_roll(ctx.slot_id, shortcut_id, result=run["dice"], ctx=ctx)
        if shortcut_id in ("sanctuary_check", "navigate", "roll_trap", "roll_loot", "boss_entry"):
            log_roll(ctx.slot_id, shortcut_id.replace("_", " "), user_message)

    ctx.refresh_deck()
    scion = get_scion(ctx)

    journal_shortcuts = ("draw_room", "draw_journal", "draw_room_journal")
    if shortcut_id in journal_shortcuts:
        prose = _maybe_ai_prose(ctx, scion, user_message, chat_provider=chat_provider)
        if prose:
            answer = prose
            if store:
                store.persist_ctx(ctx)
            return user_message, answer, sources, route

    if run.get("static"):
        if store:
            store.persist_ctx(ctx)
        return user_message, user_message, sources, route

    if story_mode == "player" and shortcut_id in journal_shortcuts:
        if store:
            store.persist_ctx(ctx)
        return user_message, user_message, sources, route

    if shortcut_id in ("dungeon_rules", "checks_help", "trials_help"):
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


def lookup_armour_from_run(run: dict[str, Any]) -> str:
    from src.games.ashes.curated import lookup_armour

    roll = run.get("armour_roll")
    if roll:
        return lookup_armour(int(roll))
    dice = run.get("dice")
    if dice and dice.get("rolls"):
        return lookup_armour(int(dice["rolls"][0]))
    return ""


def execute_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, str, list[dict], str]:
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    _ = prior_history or recent_chat_history(ctx.messages)
    return run_scion_shortcut(
        ctx,
        shortcut_id,
        chat_provider=app.chat_provider,
        retrieval_cfg=retrieval_cfg,
        top_k=app.top_k,
        factions=app.selected_factions,
    )


def try_handle_prompt(
    ctx: PlayContext,
    prompt: str,
    *,
    app: AppSession,
    prior_history: list[dict[str, str]] | None = None,
) -> tuple[str, list[dict], str] | None:
    shortcut_id = match_ashes_shortcut(prompt)
    if not shortcut_id:
        return None
    return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]


def draw_character_gift(ctx: PlayContext) -> dict:
    card_source, _, _ = get_play_settings(ctx)
    if card_source == "physical":
        raise ValueError("Physical deck mode: enter cards manually in Settings.")
    ctx.sync_deck()
    result = draw_cards(count=1, game_id=GAME_ID, char_id=ctx.slot_id or None)
    ctx.refresh_deck()
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    cards = list(result["cards"] or [])
    drawn = format_character_gift_draw(cards[0])
    scion = get_scion(ctx)
    scion.fate_gift_card = cards[0]
    scion.fate_gift = str(drawn.get("gift") or "")
    ctx.entity = scion_to_dict(scion)
    save_scion(scion)
    store = _store()
    if store:
        store.persist_ctx(ctx)
    return {"cards": cards, **drawn}


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines)
