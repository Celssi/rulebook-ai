"""Apothecaria game plugin."""

from __future__ import annotations

from src.games.apothecaria.actions import SHORTCUT_IDS, match_apothecaria_shortcut
from src.games.base import GamePlugin

GAME_ID = "apothecaria"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "apothecaria/apothecaria-pages.pdf": {
        "faction": "core",
        "label": "Apothecaria (printer-friendly)",
    },
    "apothecaria/apothecaria-commentary.pdf": {
        "faction": "supplement",
        "label": "Apothecaria Commentary",
    },
}

MVP_PDFS = [
    "apothecaria/apothecaria-pages.pdf",
]

ALL_FACTIONS = ["core", "supplement"]


class ApothecariaPlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Apothecaria",
            collection="apothecaria_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your Apothecaria witching assistant. Ask about ailments, reagents, foraging, "
            "or locales — or use shortcuts to draw patients, ailments, and locale events. "
            "Choose **AI narrator** in Settings for journal prose after each draw."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        _ = play_entity
        shortcut_id = match_apothecaria_shortcut(text)
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
        return "Full ingest (include commentary PDF)"


PLUGIN = ApothecariaPlugin()
