"""RAG query engine: retrieve from Chroma, generate with configured chat LLM."""

from __future__ import annotations

from dataclasses import dataclass

from llama_index.core.schema import NodeWithScore

from src.config import DEFAULT_GAME_ID, TOP_K_DEFAULT
from src.llm import ChatProvider, get_llamaindex_chat_llm
from src.games.base import RagContext, RetrievalBoostContext
from src.games.registry import get_game_plugin
from src.games.warhammer_40k import retrieval as r40k
from src.games.warhammer_40k.state import GameState
from src.prompts import build_system_prompt, format_context_block
from src.retrieval_core import (
    best_overlap,
    build_index,
    dedupe_nodes,
    get_collection,
    nodes_to_sources,
    query_terms,
    retrieve_hybrid,
)


@dataclass
class RagResult:
    answer: str
    sources: list[dict]
    language: str


def _format_recent_history(
    history: list[dict[str, str]] | None,
    max_messages: int = 8,
) -> str:
    if not history:
        return ""
    recent = history[-max_messages:]
    lines: list[str] = []
    for msg in recent:
        role = str(msg.get("role", "")).strip().lower()
        if role not in {"user", "assistant"}:
            continue
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        speaker = "User" if role == "user" else "Assistant"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def query(
    question: str,
    top_k: int = TOP_K_DEFAULT,
    factions: list[str] | None = None,
    game_state: GameState | None = None,
    game_id: str = DEFAULT_GAME_ID,
    chat_history: list[dict[str, str]] | None = None,
    candidate_k: int | None = None,
    use_hybrid: bool = True,
    brambletrek_character=None,
    chat_provider: ChatProvider = "ollama",
) -> RagResult:
    language = "en"
    plugin = get_game_plugin(game_id)
    context = RagContext(
        game_state=game_state,
        brambletrek_character=brambletrek_character,
    )
    effective_question = plugin.preprocess_question(question, context)

    nodes = retrieve_nodes(
        question=effective_question,
        top_k=top_k,
        factions=factions,
        game_state=game_state,
        game_id=game_id,
        candidate_k=candidate_k,
        use_hybrid=use_hybrid,
        brambletrek_character=brambletrek_character,
    )

    if not nodes:
        msg = "No matching excerpts in the index for those filters."
        return RagResult(answer=msg, sources=[], language=language)

    prompt_cap = plugin.prompt_top_k(question, top_k, context)
    prompt_nodes = nodes[:prompt_cap]
    context_block = format_context_block(prompt_nodes)
    system = build_system_prompt(
        language,
        game=game_state,
        game_id=game_id,
        brambletrek_character=brambletrek_character,
    )
    history_block = _format_recent_history(chat_history)
    history_section = (
        f"Conversation so far (for continuity only):\n{history_block}\n\n---\n\n"
        if history_block
        else ""
    )
    user_prompt = f"""Context excerpts:

{context_block}

---

{history_section}Question: {effective_question}

Answer based only on the context above."""

    llm = get_llamaindex_chat_llm(chat_provider)
    response = llm.complete(f"{system}\n\n{user_prompt}")
    answer = str(response).strip()
    return RagResult(
        answer=answer,
        sources=nodes_to_sources(prompt_nodes),
        language=language,
    )


def retrieve_nodes(
    question: str,
    top_k: int = TOP_K_DEFAULT,
    factions: list[str] | None = None,
    game_state: GameState | None = None,
    game_id: str = DEFAULT_GAME_ID,
    candidate_k: int | None = None,
    use_hybrid: bool = True,
    brambletrek_character=None,
) -> list[NodeWithScore]:
    plugin = get_game_plugin(game_id)
    context = RagContext(
        game_state=game_state,
        brambletrek_character=brambletrek_character,
    )
    search_q = plugin.enhance_query(question, context)
    keyword_definition = r40k.is_keyword_definition_question(question)
    keyword_term = r40k.extract_keyword_term(question) if keyword_definition else ""
    effective_factions = plugin.resolve_factions(question, factions, context)
    has_explicit_faction_filters = bool(factions)
    collection = get_collection(game_id)
    if collection is None:
        return []
    index = build_index(collection)

    retrieval_k = candidate_k or max(30, top_k * 6)
    nodes = retrieve_hybrid(
        game_id=game_id,
        index=index,
        collection=collection,
        query_text=search_q,
        candidate_k=retrieval_k,
        factions=effective_factions,
        use_hybrid=use_hybrid,
    )

    terms = query_terms(search_q)
    filtered_too_weak = bool(
        effective_factions
        and not has_explicit_faction_filters
        and (best_overlap(nodes[: max(6, top_k)], terms) == 0)
    )
    if filtered_too_weak:
        fallback_nodes = retrieve_hybrid(
            game_id=game_id,
            index=index,
            collection=collection,
            query_text=search_q,
            candidate_k=max(20, top_k * 4),
            factions=None,
            use_hybrid=use_hybrid,
        )
        nodes = dedupe_nodes(nodes + fallback_nodes)

    boost_ctx = RetrievalBoostContext(
        game_id=game_id,
        question=question,
        search_q=search_q,
        rag_context=context,
        collection=collection,
        index=index,
        retrieval_k=retrieval_k,
        use_hybrid=use_hybrid,
        effective_factions=effective_factions,
        keyword_definition=keyword_definition,
        keyword_term=keyword_term,
        retrieve_hybrid=retrieve_hybrid,
        dedupe_nodes=dedupe_nodes,
    )
    nodes = plugin.boost_retrieval(nodes, boost_ctx)
    result_cap = plugin.result_cap(question, top_k, context)
    return nodes[:result_cap]


def index_exists(game_id: str = DEFAULT_GAME_ID) -> bool:
    return get_collection(game_id) is not None
