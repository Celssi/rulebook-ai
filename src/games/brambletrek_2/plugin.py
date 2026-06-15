"""Brambletrek 2 game plugin."""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from src.games.base import GamePlugin, RagContext, RetrievalBoostContext
from src.games.brambletrek_2 import retrieval as bt2_rag
from src.games.brambletrek_2.actions import MULTI_DRAW_SHORTCUTS, match_brambletrek_2_shortcut

GAME_ID = "brambletrek_2"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "brambletrek_2/Brambletrek_2_-_Tales_in_the_Hundred_Acre_Woods.pdf": {
        "faction": "core",
        "label": "Brambletrek 2: Tales in the Hundred Acre Woods",
    },
}

MVP_PDFS = [
    "brambletrek_2/Brambletrek_2_-_Tales_in_the_Hundred_Acre_Woods.pdf",
]

ALL_FACTIONS = ["core"]


class Brambletrek2Plugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Brambletrek 2",
            collection="brambletrek_2_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=[],
            has_character_sheet=True,
            has_game_state=True,
        )

    @staticmethod
    def _character(context: RagContext):
        from src.games.brambletrek_2.character import character_from_dict

        if context.play_entity:
            return character_from_dict(context.play_entity)
        return None

    def enhance_query(self, question: str, context: RagContext) -> str:
        return bt2_rag.enhance_query(question, self._character(context))

    def preprocess_question(self, question: str, context: RagContext) -> str:
        return bt2_rag.preprocess_question(question, self._character(context))

    def boost_retrieval(
        self,
        nodes: list[NodeWithScore],
        boost_ctx: RetrievalBoostContext,
    ) -> list[NodeWithScore]:
        return bt2_rag.boost_retrieval(
            nodes,
            game_id=boost_ctx.game_id,
            question=boost_ctx.question,
            search_q=boost_ctx.search_q,
            collection=boost_ctx.collection,
            index=boost_ctx.index,
            retrieval_k=boost_ctx.retrieval_k,
            use_hybrid=boost_ctx.use_hybrid,
            character=self._character(boost_ctx.rag_context),
        )

    def chat_greeting(self) -> str:
        return (
            "I'm your Brambletrek 2 assistant for the Hundred Acre Woods. "
            "Ask about exploration, combat, legacies, or the Misty Hollow — "
            "or use shortcuts to draw cards for your journey."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        shortcut_id = match_brambletrek_2_shortcut(text)
        if shortcut_id in MULTI_DRAW_SHORTCUTS:
            return {
                "route": "play_multi",
                "shortcut_id": shortcut_id,
                "language": "en",
            }
        if shortcut_id in ("start_playing", "legacy_overview"):
            return {"route": "rag", "language": "en"}
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        return frozenset({"play_multi"})


PLUGIN = Brambletrek2Plugin()
