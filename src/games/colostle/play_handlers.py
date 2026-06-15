"""Play handlers (domain layer)."""

from __future__ import annotations

from typing import Any

from src.chat_history import recent_chat_history
from src.retrieval_profiles import resolve_retrieval_profile
GAME_ID = "colostle"
from src.games.colostle.actions import SHORTCUT_IDS, match_colostle_shortcut, run_shortcut
from src.games.colostle.character import (
    ColostleCharacter,
    character_from_dict,
    character_to_dict,
    class_options_payload,
    format_for_prompt,
    format_summary,
)
from src.games.colostle.lonelog import log_draw, log_narrative_line, narrative_context_for_ai, read_tail
from src.games.colostle.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.colostle.roster import create_character, delete_character, list_characters, load_character, save_character
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.llm import ChatProvider
from src.rag import query as rag_query


def _store():
    return get_play_store(GAME_ID)


def get_character(ctx: PlayContext) -> ColostleCharacter:
    return character_from_dict(ctx.entity or {})


def persist_character(ctx: PlayContext, data: dict | None = None) -> dict:
    store = _store()
    raw = data if data is not None else ctx.entity or {}
    char = character_from_dict(raw)
    char.clamp()
    if ctx.slot_id:
        char.id = ctx.slot_id
    ctx.entity = character_to_dict(char)
    save_character(char)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext) -> tuple[str, str, str]:
    store = _store()
    if not store:
        return "virtual", "player", "roomlands"
    settings = store.get_settings_ctx(ctx)
    return (
        settings.get("card_source", "virtual"),
        settings.get("story_mode", "player"),
        settings.get("location_mode", "roomlands"),
    )


def shortcut_kwargs(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    card_source, _, _ = get_play_settings(ctx)
    return {
        "char_id": ctx.slot_id or None,
        "card_source": card_source,
        "exploration_score": char.exploration_score,
    }


def character_header(ctx: PlayContext) -> dict:
    char = get_character(ctx)
    _, story_mode, location_mode = get_play_settings(ctx)
    return {
        "summary": format_summary(char),
        "name": char.name,
        "character_class": char.character_class,
        "calling": char.calling,
        "nature": char.nature,
        "exploration_score": char.exploration_score,
        "combat_score": char.combat_score,
        "wounds": char.wounds,
        "treasures": char.treasures,
        "chapter": char.chapter,
        "location_mode": location_mode,
        "last_task": char.last_task,
        "story_mode": story_mode,
    }


def character_options_payload() -> dict:
    return {"classes": class_options_payload()}


def roster_payload() -> list[dict]:
    return [{"id": e.id, "name": e.name} for e in list_characters()]


def create_character_entry(name: str) -> dict:
    char = create_character(name)
    return character_to_dict(char)


def delete_character_entry(char_id: str) -> None:
    delete_character(char_id)


def switch_character(app: AppSession, char_id: str) -> PlayContext:
    store = _store()
    if not store:
        raise RuntimeError("Colostle store unavailable")
    ctx = app.play_context(GAME_ID)
    new_ctx = store.switch_slot_ctx(ctx, char_id)
    app.play[GAME_ID] = new_ctx
    return new_ctx


def reset_character(ctx: PlayContext) -> dict:
    char = ColostleCharacter(id=ctx.slot_id or "")
    ctx.entity = character_to_dict(char)
    save_character(char)
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
    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions or None,
        game_id=GAME_ID,
        play_entity=character_to_dict(get_character(ctx)),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    return result.answer, result.sources


def _maybe_ai_prose(
    ctx: PlayContext,
    char: ColostleCharacter,
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
            adventurer_name=char.name,
            chapter=char.chapter,
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
    {"exploration_phase", "ocean_encounter", "battlements", "draw_item", "draw_event"}
)


def _apply_shortcut_state(ctx: PlayContext, run: dict) -> None:
    char = get_character(ctx)
    task = run.get("task")
    if task:
        char.last_task = str(task)
    cards = run.get("cards")
    if cards:
        char.last_cards = list(cards)
    if task == "draw_character" and run.get("draw_result"):
        fmt = run["draw_result"]
        char.calling_card = str(fmt.get("calling_card", ""))
        char.nature_card = str(fmt.get("nature_card", ""))
        char.calling = str(fmt.get("calling", ""))
        char.nature = str(fmt.get("nature", ""))
    if task == "exploration_phase":
        char.chapter = max(1, char.chapter)
    ctx.entity = character_to_dict(char)
    save_character(char)
    if ctx.slot_id and cards:
        label = str(task or "draw").replace("_", " ")
        log_draw(ctx.slot_id, label, list(cards))


def run_character_shortcut(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in SHORTCUT_IDS:
        raise ValueError(f"Unknown Colostle shortcut: {shortcut_id}")

    route = f"colostle:{shortcut_id}"
    run = run_shortcut(shortcut_id, game_id=GAME_ID, **shortcut_kwargs(ctx))
    user_message = run["user_message"]
    char = get_character(ctx)
    sources: list[dict] = []
    _, story_mode, _ = get_play_settings(ctx)

    if shortcut_id in _NARRATOR_SHORTCUTS:
        prose = _maybe_ai_prose(ctx, char, user_message, chat_provider=chat_provider)
        if prose:
            answer = prose
        elif run.get("static") or story_mode != "ai_narrator":
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
) -> tuple[str, str, list[dict], str]:
    retrieval_cfg = resolve_retrieval_profile(app.retrieval_profile)[1]
    _ = prior_history or recent_chat_history(ctx.messages)
    return run_character_shortcut(
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
    shortcut_id = match_colostle_shortcut(prompt)
    if not shortcut_id:
        return None
    return execute_shortcut(ctx, shortcut_id, app=app, prior_history=prior_history)[1:]


def shortcuts_payload() -> list[dict]:
    from src.games.colostle.actions import SHORTCUTS

    return [dict(s) for s in SHORTCUTS]


def lonelog_tail(ctx: PlayContext, n_lines: int = 50) -> list[str]:
    if not ctx.slot_id:
        return []
    return read_tail(ctx.slot_id, n_lines)
