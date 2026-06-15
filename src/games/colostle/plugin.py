"""Colostle game plugin."""

from __future__ import annotations

from src.games.base import GamePlugin
from src.games.colostle.actions import SHORTCUT_IDS, match_colostle_shortcut

GAME_ID = "colostle"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "colostle/core-rulebook.pdf": {
        "faction": "core",
        "label": "Colostle Core Rulebook",
    },
    "colostle/rules-reference.pdf": {
        "faction": "core",
        "label": "Rules Reference Sheet",
    },
    "colostle/job-pack-rules.pdf": {
        "faction": "supplement",
        "label": "Job Pack Rules",
    },
    "colostle/dungeons.pdf": {
        "faction": "supplement",
        "label": "Dungeons",
    },
    "colostle/kyodaina.pdf": {
        "faction": "supplement",
        "label": "Kyodaina",
    },
    "colostle/elite-rookhunting.pdf": {
        "faction": "supplement",
        "label": "Elite Rookhunting",
    },
}

MVP_PDFS = [
    "colostle/core-rulebook.pdf",
    "colostle/rules-reference.pdf",
]

ALL_FACTIONS = ["core", "supplement"]


class ColostlePlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Colostle",
            collection="colostle_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your Colostle adventure assistant. Ask about the rules, Rooks, and exploration — "
            "or use shortcuts to draw exploration cards, set up combat, or roll oracle answers. "
            "Choose **AI narrator** in Settings for journal prose from each draw."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        _ = play_entity
        shortcut_id = match_colostle_shortcut(text)
        if shortcut_id in SHORTCUT_IDS:
            return {
                "route": "play_multi",
                "shortcut_id": shortcut_id,
                "language": "en",
            }
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        return frozenset({"play_multi"})

    def ingest_all_label(self) -> str:
        return "Full ingest (include Job Pack, Dungeons, Kyodaina, Elite Rookhunting)"


PLUGIN = ColostlePlugin()
