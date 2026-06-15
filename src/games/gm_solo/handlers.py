"""Reusable play-handler patterns for GM solo games."""

from __future__ import annotations

from typing import Any, Callable, Protocol

from src.chat_history import recent_chat_history
from src.games.saves import AppSession, PlayContext, get_play_store
from src.games.saves.messages import append_chat_exchange
from src.llm import ChatProvider
from src.rag import query as rag_query
from src.retrieval_profiles import resolve_retrieval_profile


class GmEntity(Protocol):
    def clamp(self) -> None: ...


EntityFromDict = Callable[[dict | None], GmEntity]
EntityToDict = Callable[[GmEntity], dict]
MatchShortcut = Callable[[str], str | None]
RunShortcut = Callable[..., dict]
FormatSummary = Callable[[GmEntity], str]
SynthesizeJournal = Callable[..., str | None]


def get_entity(ctx: PlayContext, from_dict: EntityFromDict) -> GmEntity:
    return from_dict(ctx.entity or {})


def persist_entity(
    ctx: PlayContext,
    game_id: str,
    to_dict: EntityToDict,
    entity: GmEntity,
) -> dict:
    entity.clamp()
    if ctx.slot_id and hasattr(entity, "id"):
        entity.id = ctx.slot_id  # type: ignore[attr-defined]
    ctx.entity = to_dict(entity)
    store = get_play_store(game_id)
    if store:
        store.persist_ctx(ctx)
    return ctx.entity


def get_play_settings(ctx: PlayContext, game_id: str) -> tuple[str, str]:
    store = get_play_store(game_id)
    if not store:
        return "virtual", "player"
    settings = store.get_settings_ctx(ctx)
    return settings.get("card_source", "virtual"), settings.get("story_mode", "player")


def answer_prompt(
    prompt: str,
    ctx: PlayContext,
    *,
    game_id: str,
    entity_to_dict: EntityToDict,
    get_entity_fn: Callable[[PlayContext], GmEntity],
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
    chat_provider: ChatProvider,
) -> tuple[str, list[dict]]:
    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions or None,
        game_id=game_id,
        play_entity=entity_to_dict(get_entity_fn(ctx)),
        chat_provider=chat_provider,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=retrieval_cfg.get("use_hybrid", True),
        use_rerank=retrieval_cfg.get("use_rerank", False),
    )
    return result.answer, result.sources


def run_shortcut_flow(
    ctx: PlayContext,
    shortcut_id: str,
    *,
    game_id: str,
    shortcut_ids: frozenset[str],
    run_shortcut_fn: RunShortcut,
    shortcut_kwargs_fn: Callable[..., dict],
    get_entity_fn: Callable[[PlayContext], GmEntity],
    to_dict: EntityToDict,
    apply_state: Callable[[PlayContext, dict, GmEntity], None] | None,
    narrator_shortcuts: frozenset[str],
    synthesize_journal: SynthesizeJournal | None,
    log_draw: Callable[[str, str, list[str] | None], None] | None,
    chat_provider: ChatProvider,
    retrieval_cfg: dict,
    top_k: int,
    factions: list[str],
    answer_fn: Callable[..., tuple[str, list[dict]]] | None = None,
    params: dict | None = None,
) -> tuple[str, str, list[dict], str]:
    if shortcut_id not in shortcut_ids:
        raise ValueError(f"Unknown shortcut: {shortcut_id}")

    route = f"{game_id}:{shortcut_id}"
    try:
        kw = shortcut_kwargs_fn(ctx, params)
    except TypeError:
        kw = shortcut_kwargs_fn(ctx)
    run = run_shortcut_fn(shortcut_id, **kw)
    user_message = str(run["user_message"])
    entity = get_entity_fn(ctx)
    sources: list[dict] = []
    _answer = answer_fn or (
        lambda p, c, **kw: answer_prompt(
            p,
            c,
            game_id=game_id,
            entity_to_dict=to_dict,
            get_entity_fn=get_entity_fn,
            **kw,
        )
    )

    if shortcut_id in narrator_shortcuts and synthesize_journal:
        try:
            prose = synthesize_journal(user_message, entity=entity, chat_provider=chat_provider)
            if prose:
                answer = prose
            elif run.get("static"):
                answer = user_message
            else:
                rag_answer, sources = _answer(
                    str(run.get("prompt", user_message)),
                    ctx,
                    retrieval_cfg=retrieval_cfg,
                    top_k=top_k,
                    factions=factions,
                    chat_provider=chat_provider,
                )
                answer = f"{user_message}\n\n{rag_answer}"
        except Exception:
            answer = user_message
    elif run.get("static"):
        answer = user_message
    elif run.get("rag_only") or run.get("prompt"):
        rag_answer, sources = _answer(
            str(run.get("prompt", user_message)),
            ctx,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            factions=factions,
            chat_provider=chat_provider,
        )
        answer = f"{user_message}\n\n{rag_answer}" if rag_answer else user_message
    else:
        answer = user_message

    if apply_state:
        apply_state(ctx, run, entity)
    if log_draw and ctx.slot_id and run.get("cards"):
        log_draw(ctx.slot_id, str(run.get("task", shortcut_id)), list(run["cards"]))

    ctx.entity = to_dict(entity)
    store = get_play_store(game_id)
    if store:
        store.persist_ctx(ctx)
    return user_message, answer, sources, route


def make_execute_shortcut(
    game_id: str,
    shortcut_ids: frozenset[str],
    run_shortcut_flow_fn: Callable[..., tuple[str, str, list[dict], str]],
):
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
        return run_shortcut_flow_fn(
            ctx,
            shortcut_id,
            chat_provider=app.chat_provider,
            retrieval_cfg=retrieval_cfg,
            top_k=app.top_k,
            factions=app.selected_factions,
            params=params,
        )

    return execute_shortcut


def make_try_handle_prompt(
    game_id: str,
    match_fn: MatchShortcut,
    execute_fn: Callable[..., tuple[str, str, list[dict], str]],
):
    def try_handle_prompt(
        ctx: PlayContext,
        prompt: str,
        *,
        app: AppSession,
        prior_history: list[dict[str, str]] | None = None,
    ) -> tuple[str, list[dict], str] | None:
        shortcut_id = match_fn(prompt)
        if not shortcut_id:
            return None
        _user, answer, sources, route = execute_fn(
            ctx, shortcut_id, app=app, prior_history=prior_history
        )
        return answer, sources, route

    return try_handle_prompt


def append_chat(app: AppSession, ctx: PlayContext, user: str, answer: str) -> list[dict[str, str]]:
    return append_chat_exchange(app, ctx, user, answer)
