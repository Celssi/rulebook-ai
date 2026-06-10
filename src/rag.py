"""RAG query engine: retrieve from Chroma, generate with Ollama."""

from __future__ import annotations

from dataclasses import dataclass
import re

import chromadb
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.vector_stores import MetadataFilters, FilterCondition
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.llms.ollama import Ollama
from llama_index.vector_stores.chroma import ChromaVectorStore

from src.config import (
    CHAT_MODEL,
    CHROMA_DIR,
    DEFAULT_GAME_ID,
    EMBED_MODEL,
    GAME_40K,
    OLLAMA_BASE_URL,
    OLLAMA_REQUEST_TIMEOUT,
    TOP_K_DEFAULT,
    get_collection_name,
)
from src.game_state import GameState
from src.prompts import build_system_prompt, format_context_block


@dataclass
class RagResult:
    answer: str
    sources: list[dict]
    language: str


_LEXICAL_CACHE: dict[str, tuple[list[str], list[dict]]] = {}


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


def _get_collection(game_id: str = DEFAULT_GAME_ID):
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


def _build_index(collection) -> VectorStoreIndex:
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


def _faction_filters(factions: list[str] | None) -> MetadataFilters | None:
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


def _enhance_query(question: str) -> str:
    """Add keywords for common rules questions to improve retrieval."""
    lower = question.lower()
    extras: list[str] = []
    if "fight" in lower and "phase" in lower:
        extras.extend(["pile in consolidate melee attacks fight phase"])
    if "shoot" in lower and "phase" in lower:
        extras.extend(["shooting phase ranged attacks"])
    if "charge" in lower and "phase" in lower:
        extras.extend(["charge phase declare charge"])
    if "synapse" in lower:
        extras.extend(["SYNAPSE synaptic conduit Hive Mind"])
    if any(k in lower for k in ("weapon", "weapons", "wargear", "loadout")):
        extras.extend(["datasheet wargear weapons profile"])
    if "armor" in lower:
        extras.extend(["armour"])
    ability_aliases = {
        "deep strike": "deep strike deepstrike reserves reinforcements set up battlefield",
        "fights first": "fights first first strike combat interrupt",
        "feel no pain": "feel no pain ignore wounds fnp",
        "invulnerable": "invulnerable save invuln invulnerable saving throw",
        "lone operative": "lone operative cannot be targeted outside 12 inches",
        "devastating wounds": "devastating wounds mortal wounds critical wound",
        "sustained hits": "sustained hits extra hits critical hit",
        "lethal hits": "lethal hits critical hit auto wound",
        "rapid ingress": "rapid ingress reinforcements reserves end of opponent movement phase",
        "battle shock": "battleshock battle-shock leadership test objective control",
    }
    for key, alias in ability_aliases.items():
        if key in lower:
            extras.append(alias)
    if _is_keyword_definition_question(question):
        extras.extend(["core abilities keyword definition core rules"])
    if extras:
        return f"{question} {' '.join(extras)}"
    return question


_PRIMARY_RULEBOOK_SUFFIX = "Brambletrek_-_Complete_Digital_Edition.pdf"

# Printed book page numbers (as referenced in shortcuts/curated YAML).
# Mapped to PDF page indices in Complete Digital Edition via _brambletrek_pdf_page().
_BRAMBLETREK_TABLE_PAGES: dict[str, list[int]] = {
    "reason": [12],
    "background": [13],
    "trinket": [14],
    "resources": [8, 15, 16],
    "legacy": [9, 17, 18, 19, 20, 21],
    "journey": [24, 25, 26],
    "combat": [30, 31],
    "recovery": [16],
    "ending": [36],
}

# Table pages before intro/legacy overview when injecting creation context.
_BRAMBLETREK_PAGE_ORDER = [24, 25, 12, 13, 14, 15, 16, 8, 9, 17, 18, 19, 20, 21, 26, 30, 31, 36]


def _brambletrek_pdf_page(printed_page: int) -> int:
    """Convert rulebook printed page number to PDF index in Complete Digital Edition."""
    return max(1, int(printed_page) - 1)


def _brambletrek_page_sort_key(page: int) -> tuple[int, int]:
    try:
        return (_BRAMBLETREK_PAGE_ORDER.index(page), page)
    except ValueError:
        return (len(_BRAMBLETREK_PAGE_ORDER), page)


def _is_brambletrek_journey_question(question: str) -> bool:
    lower = question.lower()
    if any(
        term in lower
        for term in (
            "journey & exploration",
            "journey and exploration",
            "journey day",
            "exploration day",
            "today's journey",
            "four cards",
            "4 cards",
            "event 1",
            "clubs spades",
            "hearts diamonds",
        )
    ):
        return True
    if "journey" in lower and any(w in lower for w in ("exploration", "event", "draw order")):
        return True
    return False


def _is_brambletrek_ending_question(question: str) -> bool:
    lower = question.lower()
    return any(
        term in lower
        for term in (
            "story ending",
            "reason ending",
            "reason's ending",
            "your reason's ending",
            "end my journey",
            "end my story",
            "how does my story end",
            "how does my adventure end",
            "page 36",
            "true ending",
            "finish my journey",
        )
    )


def _is_brambletrek_adventure_question(question: str) -> bool:
    lower = question.lower()
    if any(
        name in lower
        for name in (
            "birthday of wonders",
            "pumpkin party",
            "first frost",
            "warmth of the first frost",
            "winter gift",
            "adventure module",
            "adventure act",
            "adventure scene",
        )
    ):
        return True
    return "adventure" in lower and any(
        w in lower for w in ("act", "scene", "module", "campaign", "quest")
    )


def _is_brambletrek_character_creation(question: str) -> bool:
    lower = question.lower()
    if "random gnawborn" in lower or "character creation" in lower:
        return True
    table_hits = sum(
        1 for term in ("reason for adventure", "background", "trinket") if term in lower
    )
    return table_hits >= 2 and ("resource" in lower or "legacy" in lower)


def _is_brambletrek_adventure_scene_prompt(question: str) -> bool:
    lower = question.lower()
    return "adventure scene" in lower or "adventure module text in the indexed pdf" in lower


def _brambletrek_tables_needed(
    question: str,
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> set[str]:
    lower = question.lower()
    needed: set[str] = set()
    adv_id = (
        getattr(brambletrek_character, "active_adventure", "")
        if brambletrek_character
        else ""
    )
    if any(
        term in lower
        for term in ("reason for adventure", "reason table", "reason:", "reason for my")
    ):
        needed.add("reason")
    if "background" in lower:
        needed.add("background")
    if "trinket" in lower:
        needed.add("trinket")
    if any(
        term in lower
        for term in (
            "resource",
            "health, morale",
            "morale, and supplies",
            "six resource",
            "six cards",
            "two cards per stat",
            "character resources",
        )
    ):
        needed.add("resources")
    if "legacy" in lower or any(
        name in lower
        for name in ("seer", "scrapper", "storyteller", "seeker", "sneaker", "soother")
    ):
        needed.add("legacy")
    if _is_brambletrek_journey_question(question):
        skip_journey = adv_id and (
            _is_brambletrek_adventure_scene_prompt(question)
            or _is_brambletrek_adventure_question(question)
        )
        if not skip_journey:
            needed.add("journey")
    if any(term in lower for term in ("combat setup", "initiative", "tactic card", "tactics")):
        needed.add("combat")
    if any(term in lower for term in ("health recovery", "morale recovery", "supplies recovery")):
        needed.add("recovery")
    if _is_brambletrek_ending_question(question):
        needed.add("ending")
    if _is_brambletrek_character_creation(question):
        needed |= set(_BRAMBLETREK_TABLE_PAGES.keys())
    return needed


def _is_brambletrek_card_question(question: str) -> bool:
    if _brambletrek_tables_needed(question):
        return True
    lower = question.lower()
    rank_words = ("ace", "jack", "queen", "king")
    suit_words = ("spade", "spades", "heart", "hearts", "club", "clubs", "diamond", "diamonds")
    has_rank_or_value = any(w in lower for w in rank_words) or bool(re.search(r"\b(10|[2-9])\b", lower))
    has_card_terms = "card" in lower or any(w in lower for w in suit_words)
    has_reason_terms = "reason for adventure" in lower or "reason table" in lower
    return (has_rank_or_value and has_card_terms) or has_reason_terms


def _enhance_brambletrek_query(
    question: str,
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> str:
    if _is_brambletrek_ending_question(question):
        return (
            f"{question} your reason's ending page 36 reason ending true ending "
            "continue story within Hyhill open-ended"
        )
    if brambletrek_character and getattr(brambletrek_character, "active_adventure", ""):
        from src.brambletrek_curated import adventure_meta

        adv = adventure_meta(brambletrek_character.active_adventure)
        label = adv.get("label", "")
        if label:
            question = f"{question} {label} adventure module"
    if _is_brambletrek_journey_question(question):
        adv_id = (
            getattr(brambletrek_character, "active_adventure", "")
            if brambletrek_character
            else ""
        )
        if adv_id and (
            _is_brambletrek_adventure_scene_prompt(question)
            or _is_brambletrek_adventure_question(question)
        ):
            from src.brambletrek_curated import adventure_meta

            adv = adventure_meta(adv_id)
            label = adv.get("label", "")
            return f"{question} {label} adventure scene module PDF indexed"
        return (
            f"{question} journey and exploration four cards draw order hearts diamonds "
            "clubs spades page 24 page 25 aldwund depths page 26 page 27 exit item combat"
        )
    if _is_brambletrek_character_creation(question):
        return (
            f"{question} reason for adventure background trinket character resources legacy "
            "core rulebook pages 8 12 13 14 15 16 card value ace 2-4 5-7 8-10 jack queen king "
            "maximum 20 two cards per stat"
        )
    if not _is_brambletrek_card_question(question):
        return question
    extras = "reason for adventure card value reason table character creation ace 2-4 5-7 8-10 jack queen king"
    if "background" in question.lower():
        extras += " background table card value"
    if "trinket" in question.lower():
        extras += " trinket table card value"
    if "resource" in question.lower():
        extras += " character resources health morale supplies six cards maximum 20"
    return f"{question} {extras}"


def _brambletrek_prompt_top_k(
    question: str,
    top_k: int,
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> int:
    needed = _brambletrek_tables_needed(question, brambletrek_character)
    if not needed:
        return max(top_k, 6)
    return max(top_k, min(22, top_k + len(needed) * 4))


def _brambletrek_core_page_nodes(
    game_id: str,
    collection,
    printed_pages: set[int],
) -> list[NodeWithScore]:
    """Inject chunks from Complete Digital Edition by printed rulebook page."""
    pdf_pages = {_brambletrek_pdf_page(p) for p in printed_pages}
    docs, metas = _get_lexical_corpus(game_id, collection)
    nodes: list[NodeWithScore] = []
    for text, meta in zip(docs, metas):
        if not text or not meta:
            continue
        if str(meta.get("faction", "")).lower() != "core":
            continue
        if not str(meta.get("source_file", "")).endswith(_PRIMARY_RULEBOOK_SUFFIX):
            continue
        try:
            page = int(meta.get("page", 0))
        except (TypeError, ValueError):
            continue
        if page not in pdf_pages:
            continue
        nodes.append(
            NodeWithScore(
                node=TextNode(text=str(text), metadata=meta),
                score=250.0 - page,
            )
        )
    nodes.sort(
        key=lambda n: (
            _brambletrek_page_sort_key(
                int((n.node.metadata or {}).get("page", 0) or 0) + 1
            ),
            n.get_content()[:80],
        )
    )
    return nodes


def _brambletrek_creation_table_nodes(
    game_id: str,
    collection,
    question: str,
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> list[NodeWithScore]:
    needed = _brambletrek_tables_needed(question, brambletrek_character)
    if not needed:
        return []
    pages: set[int] = set()
    for table in needed:
        pages.update(_BRAMBLETREK_TABLE_PAGES.get(table, []))
    return _brambletrek_core_page_nodes(game_id, collection, pages)


def _brambletrek_adventure_module_nodes(
    game_id: str,
    collection,
    adventure_id: str,
    *,
    limit: int = 10,
) -> list[NodeWithScore]:
    from src.brambletrek_curated import adventure_meta

    meta = adventure_meta(adventure_id)
    source_label = str(meta.get("source_label", "") or "").strip()
    if not source_label:
        return []
    page_min = meta.get("pdf_page_min")
    page_max = meta.get("pdf_page_max")
    docs, metas = _get_lexical_corpus(game_id, collection)
    nodes: list[NodeWithScore] = []
    for text, meta_row in zip(docs, metas):
        if not text or not meta_row:
            continue
        if str(meta_row.get("source_label", "")) != source_label:
            continue
        if page_min is not None and page_max is not None:
            try:
                p = int(meta_row.get("page", 0) or 0)
            except (TypeError, ValueError):
                continue
            if p < int(page_min) or p > int(page_max):
                continue
        nodes.append(
            NodeWithScore(
                node=TextNode(text=text, metadata=dict(meta_row)),
                score=1.0,
            )
        )
    nodes.sort(
        key=lambda n: int((n.node.metadata or {}).get("page", 0) or 0)
    )
    return nodes[:limit]


def _merge_factions(
    factions: list[str] | None,
    game_state: GameState | None,
) -> list[str] | None:
    if factions:
        return factions
    if game_state:
        return game_state.factions_for_retrieval()
    return None


def _is_datasheet_question(question: str) -> bool:
    lower = question.lower()
    keywords = (
        "datasheet",
        "wargear",
        "weapon",
        "weapons",
        "loadout",
        "profile",
        "deep strike",
        "ability",
        "abilities",
        "lone operative",
        "invulnerable",
        "feel no pain",
    )
    return any(k in lower for k in keywords)


def _is_keyword_definition_question(question: str) -> bool:
    lower = question.lower().strip()
    if "keyword" in lower and any(
        p in lower for p in ("explain", "define", "what is", "what does", "meaning")
    ):
        return True
    # Common form: "What does Deep Strike do?"
    if re.search(r"^what does\s+[a-z0-9 _-]{2,40}\s+do\??$", lower):
        return True
    return bool(re.search(r"^(explain|define)\s+[a-z0-9 _-]+\s+keyword\b", lower))


def _extract_keyword_term(question: str) -> str:
    lower = question.lower().strip()
    m = re.search(r"(?:explain|define)\s+([a-z][a-z0-9 _-]{1,40})\s+keyword\b", lower)
    if m:
        return m.group(1).strip().split()[-1]
    m = re.search(r"what does\s+([a-z][a-z0-9 _-]{1,40})\s+mean", lower)
    if m:
        return m.group(1).strip().split()[-1]
    m = re.search(r"what does\s+([a-z][a-z0-9 _-]{1,40})\s+do\??$", lower)
    if m:
        phrase = m.group(1).strip()
        parts = phrase.split()
        if len(parts) <= 3:
            return " ".join(parts)
        return parts[-1]
    words = _tokenize(lower)
    if "keyword" in words:
        i = words.index("keyword")
        if i > 0:
            return words[i - 1]
    return ""


def _dedupe_nodes(nodes: list[NodeWithScore]) -> list[NodeWithScore]:
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
        filters=_faction_filters(factions),
    )
    return retriever.retrieve(query_text)


def _doc_matches_factions(meta: dict | None, factions: list[str] | None) -> bool:
    if not factions:
        return True
    if not meta:
        return False
    return str(meta.get("faction", "")) in factions


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z][a-zA-Z0-9_-]+", text.lower())


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
    # Encourage documents that match a higher fraction of the query terms.
    coverage = overlap / max(1, len(terms))
    return overlap * 4.0 + freq_score + coverage * 6.0 + phrase_bonus


def _lexical_retrieve(
    game_id: str,
    collection,
    query_text: str,
    limit: int,
    factions: list[str] | None,
) -> list[NodeWithScore]:
    docs, metas = _get_lexical_corpus(game_id, collection)

    terms = _query_terms(query_text)
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


def _get_lexical_corpus(game_id: str, collection) -> tuple[list[str], list[dict]]:
    cached = _LEXICAL_CACHE.get(game_id)
    if cached is not None:
        return cached
    raw = collection.get(include=["documents", "metadatas"])
    docs = raw.get("documents") or []
    metas = raw.get("metadatas") or []
    _LEXICAL_CACHE[game_id] = (docs, metas)
    return docs, metas


def _brambletrek_reason_table_nodes(
    game_id: str,
    collection,
    limit: int = 8,
) -> list[NodeWithScore]:
    docs, metas = _get_lexical_corpus(game_id, collection)
    candidates: list[NodeWithScore] = []
    for text, meta in zip(docs, metas):
        if not text or not meta:
            continue
        if str(meta.get("faction", "")).lower() != "core":
            continue
        lower = str(text).lower()
        score = 0.0
        if "reason for adventure" in lower:
            score += 60.0
        if "card value" in lower:
            score += 35.0
        if "yearning for adventure" in lower:
            score += 15.0
        if "ace" in lower:
            score += 8.0
        if score <= 0:
            continue
        candidates.append(
            NodeWithScore(node=TextNode(text=str(text), metadata=meta), score=score)
        )
    candidates.sort(key=lambda n: n.score or 0.0, reverse=True)
    return candidates[:limit]


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


def _best_overlap(nodes: list[NodeWithScore], query_terms: set[str]) -> int:
    best = 0
    for node in nodes:
        text = node.get_content().lower()
        overlap = sum(1 for term in query_terms if term in text)
        best = max(best, overlap)
    return best


def _retrieve_hybrid(
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
        return _dedupe_nodes(dense)
    lexical = _lexical_retrieve(game_id, collection, query_text, candidate_k, factions)
    return _dedupe_nodes(_fuse_nodes_rrf(dense, lexical, candidate_k))


def _candidate_card_factions(
    question: str,
    effective_factions: list[str] | None,
) -> list[str]:
    # Prefer explicit filters if caller already constrained sources.
    if effective_factions is not None:
        cards = [f for f in effective_factions if f in {"cards_sm", "cards_nids"}]
        return cards

    lower = question.lower()
    if any(k in lower for k in ("tyranid", "hive", "synapse", "termagant", "hormagaunt")):
        return ["cards_nids"]
    if any(k in lower for k in ("space marine", "astartes", "imperium", "captain", "intercessor")):
        return ["cards_sm"]
    return ["cards_sm", "cards_nids"]


def _query_terms(question: str) -> set[str]:
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
        "with",
        "has",
    }
    return {w for w in words if len(w) >= 4 and w not in stop}


def _datasheet_score(node: NodeWithScore, terms: set[str]) -> float:
    text = node.get_content().lower().replace("armour", "armor")
    generic_terms = {
        "datasheet",
        "wargear",
        "weapon",
        "weapons",
        "loadout",
        "profile",
        "armor",
        "armour",
    }
    specific_overlap = sum(1 for t in terms if t not in generic_terms and t in text)
    generic_overlap = sum(1 for t in terms if t in generic_terms and t in text)
    table_markers = ("wargear", "ranged weapons", "melee weapons", "abilities", "keywords")
    bonus = sum(1 for m in table_markers if m in text)
    return specific_overlap * 25 + generic_overlap * 4 + bonus


def _definition_score(node: NodeWithScore, keyword_term: str) -> float:
    text = node.get_content().lower()
    meta = node.metadata or {}
    source_label = str(meta.get("source_label", "")).lower()
    faction = str(meta.get("faction", "")).lower()
    score = 0.0

    if faction == "core":
        score += 30.0
    if "core rules" in source_label or "quickstart" in source_label:
        score += 12.0
    if "core abilities" in text:
        score += 18.0
    if "core ability" in text:
        score += 10.0

    if keyword_term:
        if re.search(rf"\b{re.escape(keyword_term)}\b\s*[:\-]", text):
            score += 30.0
        term_hits = len(re.findall(rf"\b{re.escape(keyword_term)}\b", text))
        score += min(12.0, term_hits * 2.0)
    return score


def _brambletrek_card_score(node: NodeWithScore, question: str) -> float:
    lower_q = question.lower()
    text = node.get_content().lower()
    meta = node.metadata or {}
    faction = str(meta.get("faction", "")).lower()
    score = 0.0
    if faction == "core":
        score += 15.0
    if "reason for adventure" in text:
        score += 45.0
    if "card value" in text:
        score += 25.0
    if "reason table" in text:
        score += 20.0
    for token in ("ace", "jack", "queen", "king"):
        if token in lower_q and re.search(rf"\b{token}\b", text):
            score += 10.0
    return score


def query(
    question: str,
    top_k: int = TOP_K_DEFAULT,
    factions: list[str] | None = None,
    game_state: GameState | None = None,
    game_id: str = DEFAULT_GAME_ID,
    chat_history: list[dict[str, str]] | None = None,
    candidate_k: int | None = None,
    use_hybrid: bool = True,
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> RagResult:
    language = "en"
    effective_question = question
    if game_id != GAME_40K and brambletrek_character:
        from src.brambletrek_character import label_for_band
        from src.brambletrek_curated import format_reason_ending

        if _is_brambletrek_ending_question(question) and brambletrek_character.reason_band:
            reason_label = label_for_band("reasons", brambletrek_character.reason_band)
            curated = format_reason_ending(
                brambletrek_character.reason_band,
                reason_label=reason_label,
            )
            effective_question = f"{question}\n\n{curated}"

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

    # Keep internal candidate retrieval deep, but cap final prompt context.
    prompt_cap = (
        _brambletrek_prompt_top_k(question, top_k, brambletrek_character)
        if game_id != GAME_40K
        else max(top_k, 6)
    )
    prompt_nodes = nodes[:prompt_cap]
    context = format_context_block(prompt_nodes)
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

{context}

---

{history_section}Question: {effective_question}

Answer based only on the context above."""

    llm = Ollama(
        model=CHAT_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )
    response = llm.complete(
        f"{system}\n\n{user_prompt}",
    )
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
    brambletrek_character: "BrambletrekCharacter | None" = None,
) -> list[NodeWithScore]:
    search_q = (
        _enhance_query(question)
        if game_id == GAME_40K
        else _enhance_brambletrek_query(question, brambletrek_character)
    )
    keyword_definition = _is_keyword_definition_question(question)
    keyword_term = _extract_keyword_term(question) if keyword_definition else ""
    effective_factions = _merge_factions(factions, game_state) if game_id == GAME_40K else factions
    has_explicit_faction_filters = bool(factions)
    collection = _get_collection(game_id)
    if collection is None:
        return []
    index = _build_index(collection)

    retrieval_k = candidate_k or max(30, top_k * 6)
    nodes = _retrieve_hybrid(
        game_id=game_id,
        index=index,
        collection=collection,
        query_text=search_q,
        candidate_k=retrieval_k,
        factions=effective_factions,
        use_hybrid=use_hybrid,
    )

    query_terms = _query_terms(search_q)
    filtered_too_weak = bool(
        effective_factions
        and not has_explicit_faction_filters
        and (_best_overlap(nodes[: max(6, top_k)], query_terms) == 0)
    )
    if filtered_too_weak:
        fallback_nodes = _retrieve_hybrid(
            game_id=game_id,
            index=index,
            collection=collection,
            query_text=search_q,
            candidate_k=max(20, top_k * 4),
            factions=None,
            use_hybrid=use_hybrid,
        )
        nodes = _dedupe_nodes(nodes + fallback_nodes)

    if keyword_definition:
        core_nodes = _retrieve_hybrid(
            game_id=game_id,
            index=index,
            collection=collection,
            query_text=search_q,
            candidate_k=max(retrieval_k, 40),
            factions=["core"],
            use_hybrid=use_hybrid,
        )
        if core_nodes:
            ranked_core = sorted(
                _dedupe_nodes(core_nodes),
                key=lambda n: (_definition_score(n, keyword_term), n.score or 0.0),
                reverse=True,
            )
            nodes = _dedupe_nodes(ranked_core + nodes)

    if game_id == GAME_40K and _is_datasheet_question(question) and not keyword_definition:
        cards_factions = _candidate_card_factions(question, effective_factions)
        card_nodes: list[NodeWithScore] = []
        for faction in cards_factions:
            card_nodes.extend(
                _retrieve_hybrid(
                    game_id=game_id,
                    index=index,
                    collection=collection,
                    query_text=search_q,
                    candidate_k=max(retrieval_k, 30),
                    factions=[faction],
                    use_hybrid=use_hybrid,
                )
            )

        if card_nodes:
            terms = _query_terms(question)
            ranked_cards = sorted(
                _dedupe_nodes(card_nodes),
                key=lambda n: (_datasheet_score(n, terms), n.score or 0.0),
                reverse=True,
            )
            nodes = _dedupe_nodes(ranked_cards + nodes)
            nodes = nodes[: max(top_k * 2, 16)]

    if game_id != GAME_40K:
        creation_nodes = _brambletrek_creation_table_nodes(
            game_id, collection, question, brambletrek_character
        )
        if creation_nodes:
            nodes = _dedupe_nodes(creation_nodes + nodes)
        adv_id = (
            getattr(brambletrek_character, "active_adventure", "")
            if brambletrek_character
            else ""
        )
        if adv_id and (
            _is_brambletrek_adventure_question(question)
            or _is_brambletrek_adventure_scene_prompt(question)
            or not _brambletrek_tables_needed(question, brambletrek_character)
        ):
            adv_limit = 16 if _is_brambletrek_adventure_scene_prompt(question) else 12
            adv_nodes = _brambletrek_adventure_module_nodes(
                game_id, collection, adv_id, limit=adv_limit
            )
            if adv_nodes:
                nodes = _dedupe_nodes(adv_nodes + nodes)
        elif _is_brambletrek_card_question(question):
            table_nodes = _brambletrek_reason_table_nodes(game_id, collection, limit=8)
            core_nodes = _retrieve_hybrid(
                game_id=game_id,
                index=index,
                collection=collection,
                query_text=search_q,
                candidate_k=max(retrieval_k, 40),
                factions=["core"],
                use_hybrid=use_hybrid,
            )
            if core_nodes:
                ranked_core = sorted(
                    _dedupe_nodes(core_nodes),
                    key=lambda n: (_brambletrek_card_score(n, question), n.score or 0.0),
                    reverse=True,
                )
                nodes = _dedupe_nodes(table_nodes + ranked_core + nodes)

    result_cap = max(top_k * 2, 16)
    if _brambletrek_tables_needed(question, brambletrek_character):
        result_cap = max(result_cap, 28)
    if _is_brambletrek_adventure_scene_prompt(question):
        result_cap = max(result_cap, 24)
    return nodes[:result_cap]


def index_exists(game_id: str = DEFAULT_GAME_ID) -> bool:
    return _get_collection(game_id) is not None
