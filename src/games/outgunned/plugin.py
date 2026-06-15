"""Outgunned game plugin."""

from __future__ import annotations

from src.games.gm_solo.plugin_factory import build_gm_plugin
from src.games.outgunned.actions import SHORTCUT_IDS, match_outgunned_shortcut

GAME_ID = "outgunned"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "outgunned/Outgunned_Adventure_ENG_1_1.pdf": {
        "faction": "core",
        "label": "Outgunned Adventure",
    },
    "outgunned/OG_Assistent_Director_ENG_1_0.pdf": {
        "faction": "assistant_director",
        "label": "Assistant Director",
    },
    "outgunned/OG_Solo_Sheet_ENG.pdf": {
        "faction": "solo",
        "label": "Solo Sheet",
    },
}

MVP_PDFS = [
    "outgunned/Outgunned_Adventure_ENG_1_1.pdf",
    "outgunned/OG_Assistent_Director_ENG_1_0.pdf",
]

ALL_FACTIONS = ["core", "assistant_director", "solo"]

PLUGIN = build_gm_plugin(
    game_id=GAME_ID,
    label="Outgunned",
    collection="outgunned_rules",
    pdf_sources=PDF_SOURCES,
    mvp_pdfs=MVP_PDFS,
    all_factions=ALL_FACTIONS,
    match_shortcut=match_outgunned_shortcut,
    shortcut_ids=SHORTCUT_IDS,
    chat_greeting=(
        "I'm your Outgunned solo assistant. Ask about action-movie rules, Assistant Director "
        "oracles, and solo play — or use shortcuts for AD prompts, mission rolls, dice pools, "
        "and Death Roulette. Choose **AI narrator** in Settings for cinematic journal prose."
    ),
    ingest_all_label="Full ingest (Adventure + Assistant Director + Solo Sheet)",
)
