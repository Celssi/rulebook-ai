"""Shared retrieval utilities (hybrid search, Chroma access)."""

from __future__ import annotations

import re

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.vector_stores import MetadataFilters, FilterCondition
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.settings import (
    CHAT_MODEL,
    CHROMA_DIR,
    DEFAULT_GAME_ID,
    EMBED_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_REQUEST_TIMEOUT,
)

_LEXICAL_CACHE: dict[str, tuple[list[str], list[dict]]] = {}


def get_collection(game_id: str = DEFAULT_GAME_ID):
    from src.games.registry import get_collection_name

    if not CHROMA_DIR.exists():
        return None
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection_name = get_collection_name(game_id)
    try:
        collection = client.get_collection(collection_name)
    except Exception:
        return None
    if collection.count() == 0:
        return None
    return collection


def build_index(collection) -> VectorStoreIndex:
    embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
    )
    llm = Ollama(
        model=CHAT_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )
    Settings.embed_model = embed_model
    Settings.llm = llm

    vector_store = ChromaVectorStore(chroma_collection=collection)
    return VectorStoreIndex.from_vector_store(vector_store)


def faction_filters(factions: list[str] | None) -> MetadataFilters | None:
    if not factions:
        return None
    from llama_index.core.vector_stores import ExactMatchFilter

    filters = [ExactMatchFilter(key="faction", value=f) for f in factions]
    return MetadataFilters(filters=filters, condition=FilterCondition.OR)


def nodes_to_sources(nodes: list[NodeWithScore]) -> list[dict]:
    sources: list[dict] = []
    for n in nodes:
        meta = n.metadata or {}
        sources.append(
            {
                "text": n.get_content(),
                "source_file": meta.get("source_file", ""),
                "source_label": meta.get("source_label", ""),
                "page": meta.get("page", ""),
                "faction": meta.get("faction", ""),
                "score": round(n.score, 4) if n.score is not None else None,
            }
        )
    return sources


def dedupe_nodes(nodes: list[NodeWithScore]) -> list[NodeWithScore]:
    seen: set[tuple[str, str, str]] = set()
    out: list[NodeWithScore] = []
    for n in nodes:
        meta = n.metadata or {}
        key = (
            str(meta.get("source_file", "")),
            str(meta.get("page", "")),
            n.get_content()[:120],
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out


def _node_key(node: NodeWithScore) -> tuple[str, str, str]:
    meta = node.metadata or {}
    return (
        str(meta.get("source_file", "")),
        str(meta.get("page", "")),
        node.get_content()[:120],
    )


def _retrieve_dense(
    index: VectorStoreIndex,
    query_text: str,
    limit: int,
    factions: list[str] | None,
) -> list[NodeWithScore]:
    retriever = index.as_retriever(
        similarity_top_k=limit,
        filters=faction_filters(factions),
    )
    return retriever.retrieve(query_text)


def _doc_matches_factions(meta: dict | None, factions: list[str] | None) -> bool:
    if not factions:
        return True
    if not meta:
        return False
    return str(meta.get("faction", "")) in factions


def query_terms(question: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", question.lower())
    stop = {
        "what",
        "which",
        "with",
        "does",
        "have",
        "that",
        "this",
        "from",
        "unit",
        "for",
        "and",
        "the",
        "are",
        "was",
        "has",
    }
    return {w for w in words if len(w) >= 4 and w not in stop}


def _lexical_score(text: str, terms: set[str], phrase: str) -> float:
    lower = text.lower()
    if not terms:
        return 0.0
    overlap = 0
    freq_score = 0.0
    for t in terms:
        count = lower.count(t)
        if count > 0:
            overlap += 1
            freq_score += min(3, count)
    phrase_bonus = 10.0 if phrase and phrase in lower else 0.0
    coverage = overlap / max(1, len(terms))
    return overlap * 4.0 + freq_score + coverage * 6.0 + phrase_bonus


def get_lexical_corpus(game_id: str, collection) -> tuple[list[str], list[dict]]:
    cached = _LEXICAL_CACHE.get(game_id)
    if cached is not None:
        return cached
    raw = collection.get(include=["documents", "metadatas"])
    docs = raw.get("documents") or []
    metas = raw.get("metadatas") or []
    _LEXICAL_CACHE[game_id] = (docs, metas)
    return docs, metas


def _lexical_retrieve(
    game_id: str,
    collection,
    query_text: str,
    limit: int,
    factions: list[str] | None,
) -> list[NodeWithScore]:
    docs, metas = get_lexical_corpus(game_id, collection)

    terms = query_terms(query_text)
    phrase = query_text.strip().lower()
    scored: list[tuple[float, str, dict]] = []
    for text, meta in zip(docs, metas):
        if not text or not _doc_matches_factions(meta, factions):
            continue
        score = _lexical_score(str(text), terms, phrase)
        if score <= 0:
            continue
        scored.append((score, str(text), meta or {}))

    scored.sort(key=lambda x: x[0], reverse=True)
    nodes: list[NodeWithScore] = []
    for score, text, meta in scored[:limit]:
        node = TextNode(text=text, metadata=meta)
        nodes.append(NodeWithScore(node=node, score=float(score)))
    return nodes


def _fuse_nodes_rrf(
    dense_nodes: list[NodeWithScore],
    lexical_nodes: list[NodeWithScore],
    limit: int,
) -> list[NodeWithScore]:
    combined: dict[tuple[str, str, str], tuple[float, NodeWithScore]] = {}
    k = 60.0
    for rank, node in enumerate(dense_nodes, 1):
        key = _node_key(node)
        score = 1.0 / (k + rank)
        prev = combined.get(key)
        if prev is None:
            combined[key] = (score, node)
        else:
            combined[key] = (prev[0] + score, prev[1])
    for rank, node in enumerate(lexical_nodes, 1):
        key = _node_key(node)
        score = 1.0 / (k + rank)
        prev = combined.get(key)
        if prev is None:
            combined[key] = (score, node)
        else:
            combined[key] = (prev[0] + score, prev[1])

    ranked = sorted(combined.values(), key=lambda x: x[0], reverse=True)
    fused: list[NodeWithScore] = []
    for score, node in ranked[:limit]:
        node.score = round(score, 6)
        fused.append(node)
    return fused


def best_overlap(nodes: list[NodeWithScore], terms: set[str]) -> int:
    best = 0
    for node in nodes:
        text = node.get_content().lower()
        overlap = sum(1 for term in terms if term in text)
        best = max(best, overlap)
    return best


def retrieve_hybrid(
    game_id: str,
    index: VectorStoreIndex,
    collection,
    query_text: str,
    candidate_k: int,
    factions: list[str] | None,
    use_hybrid: bool = True,
) -> list[NodeWithScore]:
    dense = _retrieve_dense(index, query_text, candidate_k, factions)
    if not use_hybrid:
        return dedupe_nodes(dense)
    lexical = _lexical_retrieve(game_id, collection, query_text, candidate_k, factions)
    return dedupe_nodes(_fuse_nodes_rrf(dense, lexical, candidate_k))
