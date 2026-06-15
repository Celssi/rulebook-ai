"""Ashes game plugin."""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from src.games.ashes.actions import SHORTCUT_IDS, match_ashes_shortcut
from src.games.base import GamePlugin, RagContext, RetrievalBoostContext

GAME_ID = "ashes"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "ashes/Ashes_-_Core_Rulebook_(v1_2_0).pdf": {
        "faction": "core",
        "label": "Ashes Core Rulebook",
    },
    "ashes/Ashes_-_Multiplayer_Rules.pdf": {
        "faction": "multiplayer",
        "label": "Ashes Multiplayer Rules",
    },
}

MVP_PDFS = [
    "ashes/Ashes_-_Core_Rulebook_(v1_2_0).pdf",
]

ALL_FACTIONS = ["core", "multiplayer"]


class AshesPlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Ashes",
            collection="ashes_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
            has_game_state=False,
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your Ashes assistant for Mayfalls dungeon runs. Ask about checks, combat, "
            "or room generation — or use shortcuts to draw rooms, journal prompts, and enemies. "
            "In Settings, choose **AI narrator** for journal prose after draws, or **Player-led** "
            "to write yourself."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        _ = play_entity
        _ = play_entity
        shortcut_id = match_ashes_shortcut(text)
        if shortcut_id in SHORTCUT_IDS:
            return {
                "route": "play_multi",
                "shortcut_id": shortcut_id,
                "language": "en",
            }
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        return frozenset({"play_multi"})

    def boost_retrieval(
        self,
        nodes: list[NodeWithScore],
        boost_ctx: RetrievalBoostContext,
    ) -> list[NodeWithScore]:
        _ = boost_ctx
        return nodes

    def ingest_all_label(self) -> str:
        return "Full ingest (include multiplayer PDF)"


PLUGIN = AshesPlugin()
