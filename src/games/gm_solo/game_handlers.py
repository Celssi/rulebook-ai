"""Configurable play handlers for GM solo games."""

from __future__ import annotations

from typing import Any, Callable

from src.games.gm_solo.handlers import (
    answer_prompt,
    append_chat,
    get_entity,
    get_play_settings,
    make_execute_shortcut,
    make_try_handle_prompt,
    persist_entity,
    run_shortcut_flow,
)
from src.games.saves import AppSession, PlayContext, get_play_store
from src.llm import ChatProvider


class GmSoloHandlers:
    def __init__(
        self,
        *,
        game_id: str,
        entity_from_dict: Callable,
        entity_to_dict: Callable,
        default_entity: Callable,
        format_summary: Callable,
        format_for_prompt: Callable,
        shortcuts: list[dict],
        shortcut_ids: frozenset[str],
        match_shortcut: Callable[[str], str | None],
        run_shortcut: Callable[..., dict],
        shortcut_kwargs: Callable[[PlayContext], dict] | None = None,
        apply_shortcut_state: Callable[[PlayContext, dict, Any], None] | None = None,
        narrator_shortcuts: frozenset[str] | None = None,
        synthesize_journal: Callable[..., str | None] | None = None,
        log_draw: Callable[[str, str, list[str] | None], None] | None = None,
        read_lonelog_tail: Callable[[str, int], list[str]] | None = None,
        character_options: Callable[[], dict] | None = None,
        gm_role: str = "Game Master",
    ) -> None:
        self.game_id = game_id
        self.entity_from_dict = entity_from_dict
        self.entity_to_dict = entity_to_dict
        self.default_entity = default_entity
        self.format_summary = format_summary
        self.format_for_prompt = format_for_prompt
        self.shortcuts = shortcuts
        self.shortcut_ids = shortcut_ids
        self.match_shortcut = match_shortcut
        self.run_shortcut = run_shortcut
        self.shortcut_kwargs = shortcut_kwargs or (lambda _ctx: {})
        self.apply_shortcut_state = apply_shortcut_state
        self.narrator_shortcuts = narrator_shortcuts or frozenset()
        self.synthesize_journal = synthesize_journal
        self.log_draw = log_draw
        self.read_lonelog_tail = read_lonelog_tail
        self.character_options = character_options
        self.gm_role = gm_role

    def _store(self):
        return get_play_store(self.game_id)

    def get_character(self, ctx: PlayContext):
        return get_entity(ctx, self.entity_from_dict)

    def persist_character(self, ctx: PlayContext, data: dict | None = None) -> dict:
        raw = data if data is not None else ctx.entity or {}
        entity = self.entity_from_dict(raw)
        return persist_entity(ctx, self.game_id, self.entity_to_dict, entity)

    def reset_character(self, ctx: PlayContext) -> dict:
        entity = self.default_entity()
        if ctx.slot_id:
            entity.id = ctx.slot_id
        return persist_entity(ctx, self.game_id, self.entity_to_dict, entity)

    def character_header(self, ctx: PlayContext) -> dict:
        char = self.get_character(ctx)
        _, story_mode = get_play_settings(ctx, self.game_id)
        header = {
            "summary": self.format_summary(char),
            "name": getattr(char, "name", ""),
            "story_mode": story_mode,
        }
        if hasattr(char, "header_fields"):
            header.update(char.header_fields())
        return header

    def character_options_payload(self) -> dict:
        if self.character_options:
            return self.character_options()
        return {}

    def roster_payload(self) -> list[dict]:
        store = self._store()
        if not store:
            return []
        return [{"id": e.id, "name": e.name} for e in store.list_slots()]

    def create_character_entry(self, name: str) -> dict:
        store = self._store()
        if not store:
            raise RuntimeError(f"{self.game_id} store unavailable")
        entry = store.create_slot(name)
        return self.entity_to_dict(self.entity_from_dict(store.load_entity(entry.id)))

    def delete_character_entry(self, char_id: str) -> None:
        store = self._store()
        if store:
            store.delete_slot(char_id)

    def switch_character(self, app: AppSession, char_id: str) -> PlayContext:
        store = self._store()
        if not store:
            raise RuntimeError(f"{self.game_id} store unavailable")
        ctx = app.play_context(self.game_id)
        new_ctx = store.switch_slot_ctx(ctx, char_id)
        app.play[self.game_id] = new_ctx
        return new_ctx

    def _maybe_synthesize(self, mechanics: str, entity, chat_provider: ChatProvider) -> str | None:
        if not self.synthesize_journal:
            return None
        try:
            return self.synthesize_journal(
                mechanics,
                entity=entity,
                chat_provider=chat_provider,
            )
        except Exception:
            return None

    def run_character_shortcut(
        self,
        ctx: PlayContext,
        shortcut_id: str,
        *,
        chat_provider: ChatProvider,
        retrieval_cfg: dict,
        top_k: int,
        factions: list[str],
        params: dict | None = None,
    ) -> tuple[str, str, list[dict], str]:
        synth = None
        if self.synthesize_journal:
            synth = lambda m, entity, chat_provider: self._maybe_synthesize(m, entity, chat_provider)
        return run_shortcut_flow(
            ctx,
            shortcut_id,
            game_id=self.game_id,
            shortcut_ids=self.shortcut_ids,
            run_shortcut_fn=self.run_shortcut,
            shortcut_kwargs_fn=self.shortcut_kwargs,
            get_entity_fn=self.get_character,
            to_dict=self.entity_to_dict,
            apply_state=self.apply_shortcut_state,
            narrator_shortcuts=self.narrator_shortcuts,
            synthesize_journal=synth,
            log_draw=self.log_draw,
            chat_provider=chat_provider,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            factions=factions,
            params=params,
        )

    def execute_shortcut(
        self,
        ctx: PlayContext,
        shortcut_id: str,
        *,
        app: AppSession,
        prior_history=None,
        params: dict | None = None,
    ):
        fn = make_execute_shortcut(self.game_id, self.shortcut_ids, self.run_character_shortcut)
        return fn(ctx, shortcut_id, app=app, prior_history=prior_history, params=params)

    def try_handle_prompt(self, ctx: PlayContext, prompt: str, *, app: AppSession, prior_history=None):
        fn = make_try_handle_prompt(self.game_id, self.match_shortcut, self.execute_shortcut)
        return fn(ctx, prompt, app=app, prior_history=prior_history)

    def shortcuts_payload(self, ctx: PlayContext | None = None) -> list[dict]:
        _ = ctx
        return [dict(s) for s in self.shortcuts]

    def lonelog_tail(self, ctx: PlayContext, n_lines: int = 50) -> list[str]:
        if not ctx.slot_id:
            return []
        if self.read_lonelog_tail:
            return self.read_lonelog_tail(ctx.slot_id, n_lines)
        store = self._store()
        if store:
            return store.read_log_tail(ctx.slot_id, n_lines)
        return []

    def append_chat_exchange(self, app: AppSession, ctx: PlayContext, user: str, answer: str):
        return append_chat(app, ctx, user, answer)

    def entity_for_rag(self, ctx: PlayContext) -> dict:
        return self.entity_to_dict(self.get_character(ctx))

    def log_user_prompt(self, ctx: PlayContext, prompt: str) -> None:
        if not ctx.slot_id:
            return
        store = self._store()
        if store and store.lonelog:
            store.lonelog.log_action(ctx.slot_id, prompt[:200])
