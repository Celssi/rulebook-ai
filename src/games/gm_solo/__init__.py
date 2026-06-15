"""Shared utilities for GM-led solo play games."""

from src.games.gm_solo.dice import (
    roll_advantage_d20,
    roll_death_saves,
    reroll_outgunned_pool,
    roll_outgunned_pool,
    roll_plot_dice,
    roll_tor_skill,
    roll_year_zero,
)
from src.games.gm_solo.prompts import build_gm_solo_prompt

__all__ = [
    "build_gm_solo_prompt",
    "roll_advantage_d20",
    "roll_death_saves",
    "reroll_outgunned_pool",
    "roll_outgunned_pool",
    "roll_plot_dice",
    "roll_tor_skill",
    "roll_year_zero",
]
