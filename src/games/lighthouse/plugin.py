"""The Lighthouse at the Edge of the Universe game plugin."""

from __future__ import annotations

from src.games.base import GamePlugin
from src.games.lighthouse.actions import SHORTCUT_IDS, match_lighthouse_shortcut

GAME_ID = "lighthouse"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "lighthouse/Lighthouse_digital_spread_AccessibleVersion.pdf": {
        "faction": "core",
        "label": "Lighthouse (accessible spread)",
    },
    "lighthouse/The Lighthouse At The Edge Of The Universe - Complete Edition.pdf": {
        "faction": "core",
        "label": "Lighthouse Complete Edition",
    },
    "lighthouse/Logbook Journal.pdf": {
        "faction": "supplement",
        "label": "Logbook Journal",
    },
}

MVP_PDFS = [
    "lighthouse/Lighthouse_digital_spread_AccessibleVersion.pdf",
]

ALL_FACTIONS = ["core", "supplement"]


class LighthousePlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="The Lighthouse at the Edge of the Universe",
            collection="lighthouse_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your lighthouse keeper assistant. Ask about the rules, or use shortcuts "
            "to light the lamp, roll maintenance, observation, events, or beachcombing. "
            "Write your watch in the logbook — choose **AI narrator** in Settings for journal prose."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        _ = play_entity
        shortcut_id = match_lighthouse_shortcut(text)
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
        return "Full ingest (include logbook journal PDF)"


PLUGIN = LighthousePlugin()
