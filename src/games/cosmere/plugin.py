"""Cosmere RPG game plugin."""

from __future__ import annotations

from src.games.cosmere.actions import SHORTCUT_IDS, match_cosmere_shortcut
from src.games.gm_solo.plugin_factory import build_gm_plugin

GAME_ID = "cosmere"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "cosmere/stormlight-handbook.pdf": {
        "faction": "player",
        "label": "Cosmere RPG — Stormlight Handbook",
    },
    "cosmere/stormlight-world-guide.pdf": {
        "faction": "setting",
        "label": "Cosmere RPG — Stormlight World Guide",
    },
    "cosmere/gm-rules-overview.pdf": {
        "faction": "gm",
        "label": "Cosmere GM Rules Overview",
    },
    "cosmere/bridge-nine-adventure.pdf": {
        "faction": "adventure",
        "label": "Cosmere RPG — Bridge Nine Adventure",
    },
}

MVP_PDFS = [
    "cosmere/stormlight-handbook.pdf",
    "cosmere/gm-rules-overview.pdf",
]

ALL_FACTIONS = ["player", "setting", "gm", "adventure"]

PLUGIN = build_gm_plugin(
    game_id=GAME_ID,
    label="Cosmere RPG (Stormlight)",
    collection="cosmere_rules",
    pdf_sources=PDF_SOURCES,
    mvp_pdfs=MVP_PDFS,
    all_factions=ALL_FACTIONS,
    match_shortcut=match_cosmere_shortcut,
    shortcut_ids=SHORTCUT_IDS,
    chat_greeting=(
        "I'm your Cosmere RPG solo assistant. Ask about Stormlight rules, or use shortcuts "
        "to roll plot dice, resolve skill tests, or run combat attacks. "
        "Choose **AI narrator** in Settings for GM scene prose."
    ),
    ingest_all_label="Full ingest (handbook, world guide, GM rules, Bridge Nine)",
)
