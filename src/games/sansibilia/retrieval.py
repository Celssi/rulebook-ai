"""San Sibilia retrieval helpers."""

from __future__ import annotations

from typing import Any

from llama_index.core.schema import NodeWithScore, TextNode

_TABLE_KEYWORDS = (
    "adjective",
    "location",
    "event",
    "character table",
    "city change",
    "city changes",
    "ending",
    "end of your stay",
    "alternative endgame",
    "score",
    "day 1",
    "journal",
)


def _wants_tables(question: str) -> bool:
    lower = question.lower()
    return any(k in lower for k in _TABLE_KEYWORDS)


def _curated_snippet() -> str:
    from src.games.sansibilia.curated import format_tables_reference

    return format_tables_reference()


def enhance_query(question: str, play_entity: dict | None = None) -> str:
    _ = play_entity
    if not _wants_tables(question):
        return question
    return f"{question}\n\nReference: San Sibilia card tables and city-change rules."


def preprocess_question(question: str, play_entity: dict | None = None) -> str:
    _ = play_entity
    if not _wants_tables(question):
        return question
    return f"{question}\n\n{_curated_snippet()}"


def boost_retrieval(
    nodes: list[NodeWithScore],
    *,
    question: str,
    play_entity: dict | None = None,
) -> list[NodeWithScore]:
    _ = play_entity
    if not _wants_tables(question):
        return nodes
    snippet = _curated_snippet()
    if not snippet.strip():
        return nodes
    pinned = NodeWithScore(
        node=TextNode(text=snippet, metadata={"source_label": "curated", "page": 0}),
        score=10.0,
    )
    return [pinned, *nodes]
