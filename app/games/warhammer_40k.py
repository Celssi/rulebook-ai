"""Warhammer 40,000 Streamlit UI."""

from __future__ import annotations

import streamlit as st

from src.games.warhammer_40k.state import (
    default_state,
    format_summary,
    game_state_from_dict,
    game_state_to_dict,
)

ARMY_OPTIONS = {
    "": "—",
    "space_marines": "Space Marines",
    "tyranids": "Tyranids",
}

PHASE_OPTIONS = {
    "": "—",
    "command": "Command",
    "movement": "Movement",
    "shooting": "Shooting",
    "charge": "Charge",
    "fight": "Fight",
}

ACTIVE_OPTIONS = {
    "": "—",
    "me": "Me",
    "opponent": "Opponent",
}


def get_game_state():
    return game_state_from_dict(st.session_state.game)


def render_header() -> None:
    st.caption(
        "Personal study helper. Always verify with official rules and your judge. "
        "GW material stays local — do not share indexes."
    )
    game_state = get_game_state()
    summary = format_summary(game_state, "en")
    if summary:
        st.info(summary)


def render_game_sidebar() -> None:
    st.subheader("Game State")
    g = st.session_state.game
    g["my_army"] = st.selectbox(
        "Your Army",
        options=list(ARMY_OPTIONS.keys()),
        format_func=lambda k: ARMY_OPTIONS[k],
        index=list(ARMY_OPTIONS.keys()).index(g.get("my_army", "") or ""),
        key="game_my_army",
    )
    g["opponent_army"] = st.selectbox(
        "Opponent Army",
        options=list(ARMY_OPTIONS.keys()),
        format_func=lambda k: ARMY_OPTIONS[k],
        index=list(ARMY_OPTIONS.keys()).index(g.get("opponent_army", "") or ""),
        key="game_opponent",
    )
    g["battle_round"] = st.number_input(
        "Battle Round",
        min_value=1,
        max_value=5,
        value=int(g.get("battle_round", 1)),
        key="game_round",
    )
    g["phase"] = st.selectbox(
        "Phase",
        options=list(PHASE_OPTIONS.keys()),
        format_func=lambda k: PHASE_OPTIONS[k],
        index=list(PHASE_OPTIONS.keys()).index(g.get("phase", "") or ""),
        key="game_phase",
    )
    g["active_player"] = st.selectbox(
        "Active Player",
        options=list(ACTIVE_OPTIONS.keys()),
        format_func=lambda k: ACTIVE_OPTIONS[k],
        index=list(ACTIVE_OPTIONS.keys()).index(g.get("active_player", "") or ""),
        key="game_active",
    )
    g["notes"] = st.text_area(
        "Notes",
        value=g.get("notes", ""),
        height=80,
        key="game_notes",
    )
    if st.button("Reset Game State"):
        st.session_state.game = game_state_to_dict(default_state())
        st.rerun()
    st.session_state.game = g


def init_session_game_state() -> None:
    if "game" not in st.session_state:
        st.session_state.game = game_state_to_dict(default_state())
