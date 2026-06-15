"""Lighthouse play roster registration."""

from __future__ import annotations

from src.games.lighthouse.watch import (
    KeeperWatch,
    default_watch,
    watch_from_dict,
    watch_to_dict,
)
from src.games.saves import PlayProfile, get_play_store, register_play_profile

GAME_ID = "lighthouse"


def _slot_name(entity: KeeperWatch) -> str:
    return entity.name.strip()


def _lonelog_name(entity: KeeperWatch) -> str:
    return entity.name.strip() or "Keeper"


def _resolve_modes(ctx):
    from src.games.lighthouse import play_handlers as ph

    card_source, story_mode = ph.get_play_settings(ctx)
    return story_mode, card_source


def _entity_for_rag(ctx):
    from src.games.lighthouse import play_handlers as ph

    return watch_to_dict(ph.get_watch(ctx))


def _register() -> None:
    from src.games.lighthouse import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.lighthouse.agent import lighthouse_multi_node

        return lighthouse_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="The Lighthouse at the Edge of the Universe",
            slot_label="Watch",
            default_slot_name="",
            entity_filename="watch.json",
            entity_from_dict=watch_from_dict,
            entity_to_dict=watch_to_dict,
            default_entity=default_watch,
            slot_display_name=_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda w: w.clamp(),
            has_lonelog=True,
            play_settings={
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
            },
            session_extra_keys=[],
            resolve_play_modes=_resolve_modes,
            try_handle_prompt=ph.try_handle_prompt,
            entity_for_rag=_entity_for_rag,
            agent_multi_node=_agent_node,
        )
    )


def get_lighthouse_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Lighthouse play profile not registered")
    return store


