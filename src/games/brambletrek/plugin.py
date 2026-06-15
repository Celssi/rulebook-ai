"""Brambletrek game plugin."""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from src.games.base import GamePlugin, RagContext, RetrievalBoostContext
from src.games.brambletrek import retrieval as bt_rag
from src.games.brambletrek.actions import (
    MULTI_DRAW_SHORTCUTS,
    match_brambletrek_shortcut,
)

GAME_ID = "brambletrek"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "brambletrek/Brambletrek_-_Complete_Digital_Edition.pdf": {
        "faction": "core",
        "label": "Brambletrek Complete Digital Edition",
    },
    "brambletrek/Brambletrek_-_A_Birthday_of_Wonders.pdf": {
        "faction": "adventure",
        "label": "Brambletrek: A Birthday of Wonders",
    },
    "brambletrek/Brambletrek_-_Winter_Gift.pdf": {
        "faction": "adventure",
        "label": "Brambletrek: Winter Gift",
    },
}

MVP_PDFS = [
    "brambletrek/Brambletrek_-_Complete_Digital_Edition.pdf",
]

ALL_FACTIONS = ["core", "adventure"]


class BrambletrekPlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Brambletrek",
            collection="brambletrek_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
        )

    @staticmethod
    def _character(context: RagContext):
        from src.games.brambletrek.character import character_from_dict

        if context.play_entity:
            return character_from_dict(context.play_entity)
        return None

    def enhance_query(self, question: str, context: RagContext) -> str:
        return bt_rag.enhance_query(question, self._character(context))

    def preprocess_question(self, question: str, context: RagContext) -> str:
        return bt_rag.preprocess_question(question, self._character(context))

    def boost_retrieval(
        self,
        nodes: list[NodeWithScore],
        boost_ctx: RetrievalBoostContext,
    ) -> list[NodeWithScore]:
        return bt_rag.boost_retrieval(
            nodes,
            game_id=boost_ctx.game_id,
            question=boost_ctx.question,
            search_q=boost_ctx.search_q,
            collection=boost_ctx.collection,
            index=boost_ctx.index,
            retrieval_k=boost_ctx.retrieval_k,
            use_hybrid=boost_ctx.use_hybrid,
            brambletrek_character=self._character(boost_ctx.rag_context),
        )

    def prompt_top_k(self, question: str, top_k: int, context: RagContext) -> int:
        return bt_rag.prompt_top_k(question, top_k, self._character(context))

    def result_cap(self, question: str, top_k: int, context: RagContext) -> int:
        return bt_rag.result_cap(question, top_k, self._character(context))

    def chat_greeting(self) -> str:
        return (
            "I'm your Brambletrek rules assistant. Ask about rules or what dice "
            "results mean, and I'll answer from your indexed books. "
            "You can also roll dice or draw cards from the table deck."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        from src.games.brambletrek.character import character_from_dict

        bt = character_from_dict(play_entity) if play_entity else None
        shortcut_id = match_brambletrek_shortcut(
            text,
            active_adventure=bt.active_adventure if bt else "",
        )
        if shortcut_id in MULTI_DRAW_SHORTCUTS:
            return {
                "route": "play_multi",
                "shortcut_id": shortcut_id,
                "language": "en",
            }
        if shortcut_id == "start_playing":
            return {"route": "rag", "language": "en"}
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        return frozenset({"play_multi"})

    def ingest_all_label(self) -> str:
        return "Full ingest (include separate adventure PDFs)"


PLUGIN = BrambletrekPlugin()
