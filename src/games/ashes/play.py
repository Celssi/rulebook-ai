"""Ashes play roster registration."""

from __future__ import annotations

from src.games.ashes.scion import (
    AshesScion,
    default_scion,
    scion_from_dict,
    scion_to_dict,
)
from src.games.saves import PlayProfile, get_play_store, register_play_profile

GAME_ID = "ashes"

_JOURNAL_SETS = (
    "spirit",
    "earth",
    "ocean",
    "flame",
    "storm",
    "crypt",
    "living",
    "moon",
    "sun",
    "balance",
)


def _roster_slot_name(entity: AshesScion) -> str:
    return entity.name.strip()


def _lonelog_name(entity: AshesScion) -> str:
    return entity.name.strip() or "Scion"


def _resolve_modes(ctx):
    from src.games.ashes import play_handlers as ph

    card_source, story_mode, _ = ph.get_play_settings(ctx)
    return story_mode, card_source


def _entity_for_rag(ctx):
    from src.games.ashes import play_handlers as ph

    return scion_to_dict(ph.get_scion(ctx))


def _register() -> None:
    from src.games.ashes import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.ashes.agent import ashes_multi_node

        return ashes_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="Ashes",
            slot_label="Scion",
            default_slot_name="",
            entity_filename="scion.json",
            entity_from_dict=scion_from_dict,
            entity_to_dict=scion_to_dict,
            default_entity=default_scion,
            slot_display_name=_roster_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda s: s.clamp(),
            has_lonelog=True,
            play_settings={
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
                "prompt_set": {"default": "crypt", "choices": list(_JOURNAL_SETS)},
            },
            session_extra_keys=[],
            resolve_play_modes=_resolve_modes,
            log_user_prompt=ph.log_user_prompt,
            try_handle_prompt=ph.try_handle_prompt,
            entity_for_rag=_entity_for_rag,
            agent_multi_node=_agent_node,
        )
    )


def get_ashes_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Ashes play profile not registered")
    return store


