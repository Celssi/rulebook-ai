"""A Visit To San Sibilia game plugin."""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from src.games.base import GamePlugin, RagContext, RetrievalBoostContext
from src.games.sansibilia import retrieval as ss_rag
from src.games.sansibilia.actions import SHORTCUT_IDS, match_sansibilia_shortcut

GAME_ID = "sansibilia"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "sansibilia/Visit to San Sibilia-pages.pdf": {
        "faction": "core",
        "label": "A Visit To San Sibilia",
    },
    "sansibilia/Visit to San Sibilia - Alternative Endgame.pdf": {
        "faction": "supplement",
        "label": "Alternative Endgame Rules",
    },
}

MVP_PDFS = [
    "sansibilia/Visit to San Sibilia-pages.pdf",
]

ALL_FACTIONS = ["core", "supplement"]


class SansibiliaPlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="A Visit To San Sibilia",
            collection="sansibilia_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
        )

    def enhance_query(self, question: str, context: RagContext) -> str:
        return ss_rag.enhance_query(question, context.play_entity)

    def preprocess_question(self, question: str, context: RagContext) -> str:
        return ss_rag.preprocess_question(question, context.play_entity)

    def boost_retrieval(
        self,
        nodes: list[NodeWithScore],
        boost_ctx: RetrievalBoostContext,
    ) -> list[NodeWithScore]:
        return ss_rag.boost_retrieval(
            nodes,
            question=boost_ctx.question,
            play_entity=boost_ctx.rag_context.play_entity,
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your San Sibilia journaling assistant. Ask about the rules, card tables, "
            "or city changes — or use shortcuts to draw cards. In Settings, choose **AI narrator** "
            "to have journal prose written from each day's draw, or **Player-led** to write yourself."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        _ = play_entity
        shortcut_id = match_sansibilia_shortcut(text)
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
        return "Full ingest (include alternative endgame PDF)"


PLUGIN = SansibiliaPlugin()
