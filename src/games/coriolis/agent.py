"""Coriolis agent graph node."""

from __future__ import annotations

from src.games.coriolis.actions import SHORTCUT_IDS
from src.games.coriolis.play_handlers import HANDLERS
from src.games.gm_solo.agent_factory import build_multi_node

coriolis_multi_node = build_multi_node(
    "coriolis",
    SHORTCUT_IDS,
    HANDLERS.run_character_shortcut,
)
