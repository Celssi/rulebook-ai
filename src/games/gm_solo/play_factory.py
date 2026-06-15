"""Factory for GM solo play profile registration."""

from __future__ import annotations

from typing import Callable

from src.games.gm_solo.agent_factory import build_multi_node
from src.games.saves import PlayProfile, register_play_profile


def register_gm_play(
    *,
    game_id: str,
    game_label: str,
    slot_label: str,
    default_slot_name: str,
    entity_filename: str,
    entity_from_dict: Callable,
    entity_to_dict: Callable,
    default_entity: Callable,
    slot_display_name: Callable,
    lonelog_display_name: Callable,
    handlers,
    shortcut_ids: frozenset[str],
    play_settings: dict | None = None,
    before_save_entity: Callable | None = None,
) -> None:
    def _resolve_modes(ctx):
        from src.games.saves import get_play_store

        store = get_play_store(game_id)
        if not store:
            return "player", "virtual"
        settings = store.get_settings_ctx(ctx)
        return settings.get("story_mode", "player"), settings.get("card_source", "virtual")

    def _agent_node(state: dict) -> dict:
        return build_multi_node(game_id, shortcut_ids, handlers.run_character_shortcut)(state)

    register_play_profile(
        PlayProfile(
            game_id=game_id,
            game_label=game_label,
            slot_label=slot_label,
            default_slot_name=default_slot_name,
            entity_filename=entity_filename,
            entity_from_dict=entity_from_dict,
            entity_to_dict=entity_to_dict,
            default_entity=default_entity,
            slot_display_name=slot_display_name,
            lonelog_display_name=lonelog_display_name,
            before_save_entity=before_save_entity,
            has_lonelog=True,
            play_settings=play_settings
            or {
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
            },
            session_extra_keys=[],
            resolve_play_modes=_resolve_modes,
            log_user_prompt=handlers.log_user_prompt,
            try_handle_prompt=handlers.try_handle_prompt,
            entity_for_rag=handlers.entity_for_rag,
            agent_multi_node=_agent_node,
        )
    )
