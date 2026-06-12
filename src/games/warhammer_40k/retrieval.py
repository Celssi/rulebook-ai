"""Warhammer 40,000 retrieval helpers."""

from __future__ import annotations

import re

from llama_index.core.schema import NodeWithScore

from src.games.warhammer_40k.state import GameState


def enhance_query(question: str) -> str:
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
    if is_keyword_definition_question(question):
        extras.extend(["core abilities keyword definition core rules"])
    if extras:
        return f"{question} {' '.join(extras)}"
    return question


def infer_factions_from_text(
    text: str,
    game: GameState | None,
) -> list[str] | None:
    if game and game.my_army:
        return game.factions_for_retrieval()
    lower = text.lower()
    if any(w in lower for w in ("tyranid", "synapse", "norn", "hormagaunt", "termagant")):
        return ["tyranids", "cards_nids", "core"]
    if any(w in lower for w in ("space marine", "astartes", "oath", "terminator", "dreadnought")):
        return ["space_marines", "cards_sm", "core"]
    if any(w in lower for w in ("core", "phase", "fight", "shoot", "move", "charge")):
        return ["core"]
    return None


def is_datasheet_question(question: str) -> bool:
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


def is_keyword_definition_question(question: str) -> bool:
    lower = question.lower().strip()
    if "keyword" in lower and any(
        p in lower for p in ("explain", "define", "what is", "what does", "meaning")
    ):
        return True
    if re.search(r"^what does\s+[a-z0-9 _-]{2,40}\s+do\??$", lower):
        return True
    return bool(re.search(r"^(explain|define)\s+[a-z0-9 _-]+\s+keyword\b", lower))


def extract_keyword_term(question: str) -> str:
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
    words = query_terms(lower)
    if "keyword" in words:
        i = words.index("keyword")
        if i > 0:
            return words[i - 1]
    return ""


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


def definition_score(node: NodeWithScore, keyword_term: str) -> float:
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


def datasheet_score(node: NodeWithScore, terms: set[str]) -> float:
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


def candidate_card_factions(
    question: str,
    effective_factions: list[str] | None,
) -> list[str]:
    if effective_factions is not None:
        cards = [f for f in effective_factions if f in {"cards_sm", "cards_nids"}]
        return cards

    lower = question.lower()
    if any(k in lower for k in ("tyranid", "hive", "synapse", "termagant", "hormagaunt")):
        return ["cards_nids"]
    if any(k in lower for k in ("space marine", "astartes", "imperium", "captain", "intercessor")):
        return ["cards_sm"]
    return ["cards_sm", "cards_nids"]
