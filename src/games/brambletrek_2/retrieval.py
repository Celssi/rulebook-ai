"""Brambletrek 2 retrieval helpers."""

from __future__ import annotations

import re

from llama_index.core.schema import NodeWithScore

from src.games.brambletrek_2.character import Brambletrek2Character


def enhance_query(question: str, character: Brambletrek2Character | None) -> str:
    lower = question.lower()
    extra: list[str] = []
    if any(t in lower for t in ("exploration", "journey day", "four cards", "woods")):
        extra.append("exploration tables Hundred Acre Woods")
    if any(t in lower for t in ("hollow", "misty", "memory fragment")):
        extra.append("Misty Hollow memory fragments")
    if any(t in lower for t in ("combat", "tactic", "opponent", "initiative")):
        extra.append("combat encounter opponent tactics")
    if any(t in lower for t in ("legacy", "pooh", "piglet", "gnawborn")):
        extra.append("legacy character abilities")
    if character and character.legacy:
        extra.append(f"legacy {character.legacy}")
    if not extra:
        return question
    return question + " " + " ".join(extra)


def preprocess_question(question: str, character: Brambletrek2Character | None) -> str:
    return question


def boost_retrieval(
    nodes: list[NodeWithScore],
    *,
    game_id: str,
    question: str,
    search_q: str,
    collection: str,
    index,
    retrieval_k: int,
    use_hybrid: bool,
    character: Brambletrek2Character | None,
) -> list[NodeWithScore]:
    _ = (game_id, search_q, collection, index, retrieval_k, use_hybrid, character)
    lower = question.lower()
    if not nodes:
        return nodes
    scored: list[tuple[float, NodeWithScore]] = []
    for n in nodes:
        text = (n.node.get_content() or "").lower()
        boost = 0.0
        if "hundred acre" in lower and "hundred acre" in text:
            boost += 0.05
        if "misty hollow" in lower and "hollow" in text:
            boost += 0.05
        if character and character.in_hollow and "hollow" in text:
            boost += 0.03
        scored.append((float(n.score or 0) + boost, n))
    scored.sort(key=lambda x: x[0], reverse=True)
    out = []
    for score, n in scored:
        n.score = score
        out.append(n)
    return out
