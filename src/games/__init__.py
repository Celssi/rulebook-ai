"""Per-game plugins and registry."""

from src.games.registry import (
    all_game_ids,
    game_options,
    get_game_config,
    get_game_plugin,
)

__all__ = [
    "all_game_ids",
    "game_options",
    "get_game_config",
    "get_game_plugin",
]
