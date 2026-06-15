"""Whispers play roster registration."""

from __future__ import annotations

from src.games.saves import PlayProfile, get_play_store, register_play_profile
from src.games.whispers.investigation import (
    WhispersInvestigation,
    default_investigation,
    investigation_from_dict,
    investigation_to_dict,
)

GAME_ID = "whispers"


def _roster_slot_name(entity: WhispersInvestigation) -> str:
    return entity.investigator_name.strip() or entity.location_name.strip()


def _lonelog_name(entity: WhispersInvestigation) -> str:
    return entity.investigator_name.strip() or "Investigator"


def _resolve_modes(ctx):
    from src.games.whispers import play_handlers as ph

    card_source, story_mode, _ = ph.get_play_settings(ctx)
    return story_mode, card_source


def _entity_for_rag(ctx):
    from src.games.whispers import play_handlers as ph

    return investigation_to_dict(ph.get_investigation(ctx))


def _register() -> None:
    from src.games.whispers import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.whispers.agent import whispers_multi_node

        return whispers_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="Whispers in the Walls",
            slot_label="Investigation",
            default_slot_name="",
            entity_filename="investigation.json",
            entity_from_dict=investigation_from_dict,
            entity_to_dict=investigation_to_dict,
            default_entity=default_investigation,
            slot_display_name=_roster_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda v: v.clamp(),
            has_lonelog=True,
            play_settings={
                "story_mode": {"default": "player", "choices": ["player", "ai_narrator"]},
                "card_source": {"default": "virtual", "choices": ["physical", "virtual"]},
                "difficulty": {"default": "normal", "choices": ["normal", "easy"]},
            },
            session_extra_keys=[],
            resolve_play_modes=_resolve_modes,
            log_user_prompt=ph.log_user_prompt,
            try_handle_prompt=ph.try_handle_prompt,
            entity_for_rag=_entity_for_rag,
            agent_multi_node=_agent_node,
        )
    )


def get_whispers_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("Whispers play profile not registered")
    return store


