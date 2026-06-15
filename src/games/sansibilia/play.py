"""San Sibilia play roster registration."""

from __future__ import annotations

from src.games.sansibilia.visit import (
    SansibiliaVisit,
    default_visit,
    visit_from_dict,
    visit_to_dict,
)
from src.games.saves import PlayProfile, get_play_store, register_play_profile

GAME_ID = "sansibilia"


def _roster_slot_name(entity: SansibiliaVisit) -> str:
    return entity.name.strip()


def _lonelog_name(entity: SansibiliaVisit) -> str:
    return entity.name.strip() or "Visitor"


def _resolve_modes(ctx):
    from src.games.sansibilia import play_handlers as ph

    _, card_source, story_mode = ph.get_play_settings(ctx)
    return story_mode, card_source


def _entity_for_rag(ctx):
    from src.games.sansibilia import play_handlers as ph

    return visit_to_dict(ph.get_visit(ctx))


def _register() -> None:
    from src.games.sansibilia import play_handlers as ph

    def _agent_node(state: dict) -> dict:
        from src.games.sansibilia.agent import sansibilia_multi_node

        return sansibilia_multi_node(state)

    register_play_profile(
        PlayProfile(
            game_id=GAME_ID,
            game_label="A Visit To San Sibilia",
            slot_label="Visit",
            default_slot_name="",
            entity_filename="visit.json",
            entity_from_dict=visit_from_dict,
            entity_to_dict=visit_to_dict,
            default_entity=default_visit,
            slot_display_name=_roster_slot_name,
            lonelog_display_name=_lonelog_name,
            before_save_entity=lambda v: v.clamp(),
            has_lonelog=True,
            play_settings={
                "ending_mode": {"default": "four_changes", "choices": ["four_changes", "score_90"]},
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


def get_sansibilia_store():
    store = get_play_store(GAME_ID)
    if store is None:
        raise RuntimeError("San Sibilia play profile not registered")
    return store


