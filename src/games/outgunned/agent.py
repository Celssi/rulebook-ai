"""Outgunned agent graph node."""

from __future__ import annotations

from src.games.gm_solo.agent_factory import build_multi_node
from src.games.outgunned.actions import SHORTCUT_IDS
from src.games.outgunned.play_handlers import HANDLERS

outgunned_multi_node = build_multi_node(
    "outgunned",
    SHORTCUT_IDS,
    HANDLERS.run_character_shortcut,
)
