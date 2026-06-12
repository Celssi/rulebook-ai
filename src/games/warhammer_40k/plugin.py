"""Warhammer 40,000 game plugin."""

from __future__ import annotations

from llama_index.core.schema import NodeWithScore

from src.settings import CURATED_DIR, LEVIATHAN_YAML
from src.games.base import GamePlugin, RagContext, RetrievalBoostContext
from src.games.warhammer_40k import retrieval as r40k
from src.games.warhammer_40k.state import GameState

GAME_ID = "40k"

PDF_SOURCES: dict[str, dict[str, str]] = {
    "40k/Warhammer-40k-Quickstart-Guide.pdf": {
        "faction": "core",
        "label": "Quickstart Guide",
    },
    "40k/Warhammer-40k-Core-Rules.pdf": {
        "faction": "core",
        "label": "Core Rules",
    },
    "40k/Adeptus Astartes Cards.pdf": {
        "faction": "cards_sm",
        "label": "Space Marines Cards",
    },
    "40k/Tyranid Cards.pdf": {
        "faction": "cards_nids",
        "label": "Tyranid Cards",
    },
    "40k/Codex - Space Marines (10th Edition).pdf": {
        "faction": "space_marines",
        "label": "Codex Space Marines",
    },
    "40k/Codex - Tyranids (10th Edition).pdf": {
        "faction": "tyranids",
        "label": "Codex Tyranids",
    },
}

MVP_PDFS = [
    "40k/Warhammer-40k-Quickstart-Guide.pdf",
    "40k/Warhammer-40k-Core-Rules.pdf",
    "40k/Adeptus Astartes Cards.pdf",
    "40k/Tyranid Cards.pdf",
]

ALL_FACTIONS = ["core", "space_marines", "tyranids", "cards_sm", "cards_nids"]

OCR_PDFS = [
    "40k/Codex - Tyranids (10th Edition).pdf",
]


class Warhammer40kPlugin(GamePlugin):
    def __init__(self) -> None:
        super().__init__(
            game_id=GAME_ID,
            label="Warhammer 40,000",
            collection="40k_rules",
            pdf_sources=PDF_SOURCES,
            mvp_pdfs=MVP_PDFS,
            all_factions=ALL_FACTIONS,
            ocr_pdfs=OCR_PDFS,
            has_game_state=True,
        )

    def enhance_query(self, question: str, context: RagContext) -> str:
        return r40k.enhance_query(question)

    def resolve_factions(
        self,
        question: str,
        factions: list[str] | None,
        context: RagContext,
    ) -> list[str] | None:
        if factions:
            return factions
        if context.game_state:
            return context.game_state.factions_for_retrieval()
        return factions

    def boost_retrieval(
        self,
        nodes: list[NodeWithScore],
        boost_ctx: RetrievalBoostContext,
    ) -> list[NodeWithScore]:
        dedupe = boost_ctx.dedupe_nodes
        retrieve = boost_ctx.retrieve_hybrid

        if boost_ctx.keyword_definition:
            core_nodes = retrieve(
                game_id=boost_ctx.game_id,
                index=boost_ctx.index,
                collection=boost_ctx.collection,
                query_text=boost_ctx.search_q,
                candidate_k=max(boost_ctx.retrieval_k, 40),
                factions=["core"],
                use_hybrid=boost_ctx.use_hybrid,
            )
            if core_nodes:
                ranked_core = sorted(
                    dedupe(core_nodes),
                    key=lambda n: (
                        r40k.definition_score(n, boost_ctx.keyword_term),
                        n.score or 0.0,
                    ),
                    reverse=True,
                )
                nodes = dedupe(ranked_core + nodes)

        if r40k.is_datasheet_question(boost_ctx.question) and not boost_ctx.keyword_definition:
            cards_factions = r40k.candidate_card_factions(
                boost_ctx.question, boost_ctx.effective_factions
            )
            card_nodes: list[NodeWithScore] = []
            for faction in cards_factions:
                card_nodes.extend(
                    retrieve(
                        game_id=boost_ctx.game_id,
                        index=boost_ctx.index,
                        collection=boost_ctx.collection,
                        query_text=boost_ctx.search_q,
                        candidate_k=max(boost_ctx.retrieval_k, 30),
                        factions=[faction],
                        use_hybrid=boost_ctx.use_hybrid,
                    )
                )
            if card_nodes:
                terms = r40k.query_terms(boost_ctx.question)
                ranked_cards = sorted(
                    dedupe(card_nodes),
                    key=lambda n: (r40k.datasheet_score(n, terms), n.score or 0.0),
                    reverse=True,
                )
                nodes = dedupe(ranked_cards + nodes)
        return nodes

    def chat_greeting(self) -> str:
        return (
            "I'm your Warhammer 40k rules assistant. Ask about rules, units, or "
            "what's in the Leviathan box — I'll search your indexed documents. "
            "You can also roll dice (e.g. roll 2d6) or draw cards."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        brambletrek_character: dict | None = None,
    ) -> dict | None:
        from src.tools import is_leviathan_list_question

        if is_leviathan_list_question(text):
            return {"route": "leviathan", "language": "en"}
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        return frozenset({"leviathan"})

    def ingest_all_label(self) -> str:
        return "Full ingest (include codexes)"


PLUGIN = Warhammer40kPlugin()
