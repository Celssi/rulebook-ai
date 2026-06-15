"""The One Ring game plugin."""

from __future__ import annotations

from src.games.gm_solo.plugin_factory import build_gm_plugin
from src.games.tor.actions import SHORTCUT_IDS, match_tor_shortcut

GAME_ID = "tor"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "tor/core.pdf": {
        "faction": "core",
        "label": "The One Ring 2e — Core Rulebook",
    },
    "tor/strider_mode.pdf": {
        "faction": "strider_mode",
        "label": "The One Ring 2e — Strider Mode",
    },
    "tor/gm.pdf": {
        "faction": "gm",
        "label": "The One Ring 2e — Loremaster's Screen",
    },
}

MVP_PDFS = [
    "tor/strider_mode.pdf",
    "tor/core.pdf",
]

ALL_FACTIONS = ["core", "strider_mode", "gm"]

PLUGIN = build_gm_plugin(
    game_id=GAME_ID,
    label="The One Ring (Strider Mode)",
    collection="tor_rules",
    pdf_sources=PDF_SOURCES,
    mvp_pdfs=MVP_PDFS,
    all_factions=ALL_FACTIONS,
    match_shortcut=match_tor_shortcut,
    shortcut_ids=SHORTCUT_IDS,
    chat_greeting=(
        "I'm your One Ring solo assistant for Strider Mode. Ask about Middle-earth rules, "
        "or use shortcuts for the Telling Table, Lore Table, patron quests, Fortune, skill rolls, "
        "and journey events. Choose **AI narrator** in Settings for GM scene prose."
    ),
    ingest_all_label="Full ingest (Core, Strider Mode, Loremaster's Screen)",
)
