"""Whispers in the Walls game plugin."""

from __future__ import annotations

from src.games.base import GamePlugin
from src.games.whispers.actions import SHORTCUT_IDS, match_whispers_shortcut

GAME_ID = "whispers"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "whispers/Whispers In the Walls 2e - Pages.pdf": {
        "faction": "core",
        "label": "Whispers in the Walls (2e)",
    },
    "whispers/WhispersInTheWalls2e - Player Journal.pdf": {
        "faction": "journal",
        "label": "Player Journal",
    },
}

MVP_PDFS = [
    "whispers/Whispers In the Walls 2e - Pages.pdf",
]

ALL_FACTIONS = ["core", "journal"]


class WhispersPlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Whispers in the Walls",
            collection="whispers_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your Whispers in the Walls assistant. Ask about the rules, card tables, "
            "or use shortcuts to build your Whispers deck and draw prompts. "
            "In Settings, choose **AI narrator** for journal prose after each draw, "
            "or **Player-led** to write yourself."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        _ = play_entity
        shortcut_id = match_whispers_shortcut(text)
        if shortcut_id in SHORTCUT_IDS:
            return {
                "route": "play_multi",
                "shortcut_id": shortcut_id,
                "language": "en",
            }
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        return frozenset({"play_multi"})


PLUGIN = WhispersPlugin()
