"""Game plugin protocol and shared context types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Protocol

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore

if TYPE_CHECKING:
    from src.games.warhammer_40k.state import GameState


@dataclass
class RagContext:
    """Optional per-query context passed to game retrieval hooks."""

    game_state: GameState | None = None
    play_entity: dict | None = None


@dataclass
class RetrievalBoostContext:
    """Inputs for game-specific retrieval boosting after hybrid search."""

    game_id: str
    question: str
    search_q: str
    rag_context: RagContext
    collection: Any
    index: VectorStoreIndex
    retrieval_k: int
    use_hybrid: bool
    effective_factions: list[str] | None
    keyword_definition: bool
    keyword_term: str
    retrieve_hybrid: Callable[..., list[NodeWithScore]]
    dedupe_nodes: Callable[[list[NodeWithScore]], list[NodeWithScore]]


@dataclass
class GamePlugin:
    """Static metadata plus optional hooks for a supported game."""

    game_id: str
    label: str
    collection: str
    pdf_sources: dict[str, dict[str, str]]
    mvp_pdfs: list[str]
    all_factions: list[str]
    ocr_pdfs: list[str] = field(default_factory=list)
    has_game_state: bool = False
    has_character_sheet: bool = False

    def enhance_query(self, question: str, context: RagContext) -> str:
        return question

    def preprocess_question(self, question: str, context: RagContext) -> str:
        """Adjust question before retrieval (e.g. inject curated snippets)."""
        return question

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
        """Adjust node order after hybrid search and optional cross-encoder rerank."""
        return nodes

    def prompt_top_k(self, question: str, top_k: int, context: RagContext) -> int:
        return max(top_k, 6)

    def result_cap(self, question: str, top_k: int, context: RagContext) -> int:
        return max(top_k * 2, 16)

    def chat_greeting(self) -> str:
        return (
            "I'm your rules assistant. Ask about rules from your indexed documents. "
            "You can also roll dice or draw cards."
        )

    def route_before_generic(
        self,
        text: str,
        *,
        play_entity: dict | None = None,
    ) -> dict | None:
        """Return router state overrides, or None to continue generic routing."""
        return None

    def agent_direct_routes(self) -> frozenset[str]:
        """Routes whose tool output is returned without a second LLM pass."""
        return frozenset()

    def ingest_all_label(self) -> str:
        return "Full ingest (all PDFs)"


class AgentNodeFn(Protocol):
    def __call__(self, state: dict) -> dict: ...
