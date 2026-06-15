"""Apothecaria play roster registration."""

from __future__ import annotations

from src.games.apothecaria.cottage import (
    WitchCottage,
    cottage_from_dict,
    cottage_to_dict,
    default_cottage,
)
from src.games.saves import PlayProfile, get_play_store, register_play_profile

GAME_ID = "apothecaria"


def _slot_name(entity: WitchCottage) -> str:
    return entity.name.strip()


def _lonelog_name(entity: WitchCottage) -> str:
    return entity.name.strip() or "Witch"


def _resolve_modes(ctx):
    from src.games.apothecaria import play_handlers as ph

    card_source, story_mode = ph.get_play_settings(ctx)
    return story_mode, card_source


def _entity_for_rag(ctx):
    from src.games.apothecaria import play_handlers as ph

    return cottage_to_dict(ph.get_cottage(ctx))


def _register() -> None:
    from src.games.apothecaria import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.apothecaria.agent import apothecaria_multi_node

        return apothecaria_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="Apothecaria",
            slot_label="Cottage",
            default_slot_name="",
            entity_filename="cottage.json",
            entity_from_dict=cottage_from_dict,
            entity_to_dict=cottage_to_dict,
            default_entity=default_cottage,
            slot_display_name=_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda c: c.clamp(),
            has_lonelog=True,
            play_settings={
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
            },
            session_extra_keys=[],
            resolve_play_modes=_resolve_modes,
            log_user_prompt=ph.log_user_prompt,
            try_handle_prompt=ph.try_handle_prompt,
            entity_for_rag=_entity_for_rag,
            agent_multi_node=_agent_node,
        )
    )


def get_apothecaria_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Apothecaria play profile not registered")
    return store


