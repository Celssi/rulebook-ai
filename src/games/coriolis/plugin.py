"""Coriolis: The Great Dark game plugin."""

from __future__ import annotations

from src.games.gm_solo.plugin_factory import build_gm_plugin
from src.games.coriolis.actions import SHORTCUT_IDS, match_coriolis_shortcut

GAME_ID = "coriolis"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "coriolis/Coriolis_The_Great_Dark_Core_Rulebook.pdf": {
        "faction": "core",
        "label": "Coriolis: The Great Dark — Core Rulebook",
    },
    "coriolis/Flowers of Algorab campaign book v1.1.pdf": {
        "faction": "campaign",
        "label": "Flowers of Algorab (campaign)",
    },
}

MVP_PDFS = [
    "coriolis/Coriolis_The_Great_Dark_Core_Rulebook.pdf",
]

ALL_FACTIONS = ["core", "campaign"]

PLUGIN = build_gm_plugin(
    game_id=GAME_ID,
    label="Coriolis: The Great Dark",
    collection="coriolis_rules",
    pdf_sources=PDF_SOURCES,
    mvp_pdfs=MVP_PDFS,
    all_factions=ALL_FACTIONS,
    match_shortcut=match_coriolis_shortcut,
    shortcut_ids=SHORTCUT_IDS,
    chat_greeting=(
        "I'm your Coriolis: The Great Dark solo assistant. Ask about the Lost Horizon, "
        "Explorers Guild play, attribute and gear dice, crew and Bird — or use shortcuts "
        "for rolls, pushed rolls, despair checks, and encounters. Choose **AI narrator** "
        "in Settings for scene prose."
    ),
    ingest_all_label="Full ingest (core + Flowers of Algorab campaign)",
)
