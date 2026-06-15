"""Registry consistency tests."""

from __future__ import annotations

from src.games.registry import GAME_CATALOG, all_game_ids
from src.games.saves import all_play_profiles, get_play_profile


def test_all_plugins_in_catalog() -> None:
    for game_id in all_game_ids():
        assert game_id in GAME_CATALOG


def test_play_profiles_have_agent_nodes() -> None:
    for game_id, profile in all_play_profiles().items():
        assert profile.agent_multi_node is not None, f"{game_id} missing agent_multi_node"
        assert profile.resolve_play_modes is not None, f"{game_id} missing resolve_play_modes"
        assert profile.entity_for_rag is not None, f"{game_id} missing entity_for_rag"


def test_play_profile_matches_plugin_character_sheet() -> None:
    from src.games.registry import get_game_plugin

    for game_id, profile in all_play_profiles().items():
        plugin = get_game_plugin(game_id)
        assert plugin.has_character_sheet, f"{game_id} play profile without character sheet flag"
        assert get_play_profile(game_id) is profile
