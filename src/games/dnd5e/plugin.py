"""D&D 5e game plugin."""

from __future__ import annotations

from src.games.dnd5e.actions import SHORTCUT_IDS, match_dnd5e_shortcut
from src.games.gm_solo.plugin_factory import build_gm_plugin

GAME_ID = "dnd5e"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "dnd5e/player.pdf": {
        "faction": "player",
        "label": "Player's Handbook (2024)",
    },
    "dnd5e/dm.pdf": {
        "faction": "dm",
        "label": "Dungeon Master's Guide (2024)",
    },
    "dnd5e/monsters.pdf": {
        "faction": "monsters",
        "label": "Monster Manual (2024)",
    },
    "dnd5e/heroes_faerun.pdf": {
        "faction": "heroes_faerun",
        "label": "Heroes of Faerûn",
    },
    "dnd5e/adventures_faerun.pdf": {
        "faction": "adventures_faerun",
        "label": "Adventures in Faerûn",
    },
}

MVP_PDFS = [
    "dnd5e/player.pdf",
    "dnd5e/dm.pdf",
]

ALL_FACTIONS = ["player", "dm", "monsters", "heroes_faerun", "adventures_faerun"]

PLUGIN = build_gm_plugin(
    game_id=GAME_ID,
    label="D&D 5e solo",
    collection="dnd5e_rules",
    pdf_sources=PDF_SOURCES,
    mvp_pdfs=MVP_PDFS,
    all_factions=ALL_FACTIONS,
    match_shortcut=match_dnd5e_shortcut,
    shortcut_ids=SHORTCUT_IDS,
    chat_greeting=(
        "I'm your D&D 5e solo assistant. Ask about rules, run a freeform homebrew campaign, "
        "or set **Campaign** to Faerûn in Character settings for Forgotten Realms lore. "
        "Shortcuts cover ability checks, saves, attacks, initiative, death saves, and rests. "
        "Choose **AI narrator** in Settings for DM scene prose."
    ),
    ingest_all_label="Full ingest (PHB, DMG, MM, Heroes of Faerûn, Adventures in Faerûn)",
)
