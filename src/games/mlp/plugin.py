"""My Little Pony RPG game plugin."""

from __future__ import annotations

from src.games.gm_solo.plugin_factory import build_gm_plugin
from src.games.mlp.actions import SHORTCUT_IDS, match_mlp_shortcut

GAME_ID = "mlp"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "mlp/core-rulebook.pdf": {
        "faction": "core",
        "label": "My Little Pony RPG — Core Rulebook",
    },
    "mlp/encounters-in-ponyville.pdf": {
        "faction": "encounters",
        "label": "MLP — Encounters in Ponyville",
    },
}

MVP_PDFS = [
    "mlp/core-rulebook.pdf",
]

ALL_FACTIONS = ["core", "encounters"]

PLUGIN = build_gm_plugin(
    game_id=GAME_ID,
    label="My Little Pony RPG",
    collection="mlp_rules",
    pdf_sources=PDF_SOURCES,
    mvp_pdfs=MVP_PDFS,
    all_factions=ALL_FACTIONS,
    match_shortcut=match_mlp_shortcut,
    shortcut_ids=SHORTCUT_IDS,
    chat_greeting=(
        "I'm your My Little Pony RPG solo assistant. Ask about the rules, or use shortcuts "
        "for Skill Tests, spellcasting tracking, Friendship Points, and encounters. "
        "Choose **AI narrator** in Settings for story prose."
    ),
    ingest_all_label="Full ingest (core rulebook + Encounters in Ponyville)",
)
