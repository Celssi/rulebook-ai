"""Evaluate retrieval recall against a small regression set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import DEFAULT_GAME_ID, GAME_BRAMBLETREK, GAME_BRAMBLETREK_2
from src.rag import nodes_to_sources, retrieve_nodes

DEFAULT_CASES = ROOT / "data" / "eval" / "retrieval_regression.json"
BRAMBLETREK_CASES = ROOT / "data" / "eval" / "brambletrek_retrieval_regression.json"
BRAMBLETREK_2_CASES = ROOT / "data" / "eval" / "brambletrek_2_retrieval_regression.json"
GM_SOLO_CASES: dict[str, Path] = {
    "outgunned": ROOT / "data" / "eval" / "outgunned_retrieval_regression.json",
    "tor": ROOT / "data" / "eval" / "tor_retrieval_regression.json",
    "coriolis": ROOT / "data" / "eval" / "coriolis_retrieval_regression.json",
    "cosmere": ROOT / "data" / "eval" / "cosmere_retrieval_regression.json",
    "mlp": ROOT / "data" / "eval" / "mlp_retrieval_regression.json",
    "dnd5e": ROOT / "data" / "eval" / "dnd5e_retrieval_regression.json",
}


def _load_cases(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Cases file must contain a JSON list.")
    return data


def _score_case(sources: list[dict], expected_terms: list[str]) -> tuple[bool, float]:
    haystack = " ".join(str(src.get("text", "")).lower() for src in sources)
    if not expected_terms:
        return bool(sources), 1.0 if sources else 0.0
    matched = [term for term in expected_terms if term.lower() in haystack]
    hit = len(matched) > 0
    coverage = len(matched) / max(1, len(expected_terms))
    return hit, coverage


def _has_core_in_top_n(sources: list[dict], top_n: int) -> bool:
    return any(
        str(src.get("faction", "")).lower() == "core"
        for src in sources[: max(1, top_n)]
    )


def _has_faction_in_top_n(sources: list[dict], top_n: int, faction: str) -> bool:
    want = faction.lower()
    return any(
        str(src.get("faction", "")).lower() == want for src in sources[: max(1, top_n)]
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate retrieval recall@k for regression queries")
    parser.add_argument(
        "--game",
        default=DEFAULT_GAME_ID,
        help="Game id to evaluate (e.g. 40k, brambletrek).",
    )
    parser.add_argument(
        "--cases",
        type=Path,
        default=None,
        help="JSON file with queries and expected_terms",
    )
    parser.add_argument("--top-k", type=int, default=8, help="Final returned context size")
    parser.add_argument(
        "--candidate-k",
        type=int,
        default=40,
        help="Internal candidate pool size before ranking",
    )
    parser.add_argument(
        "--no-hybrid",
        action="store_true",
        help="Disable lexical+dense fusion and run dense-only retrieval",
    )
    parser.add_argument(
        "--use-rerank",
        action="store_true",
        help="Enable cross-encoder reranking after hybrid retrieval",
    )
    args = parser.parse_args()

    case_path = args.cases
    if case_path is None:
        if args.game == GAME_BRAMBLETREK:
            case_path = BRAMBLETREK_CASES
        elif args.game == GAME_BRAMBLETREK_2:
            case_path = BRAMBLETREK_2_CASES
        elif args.game in GM_SOLO_CASES:
            case_path = GM_SOLO_CASES[args.game]
        else:
            case_path = DEFAULT_CASES
    cases = _load_cases(case_path)
    hits = 0
    total_coverage = 0.0
    ordering_checks = 0
    ordering_passes = 0

    mode = "hybrid"
    if args.no_hybrid:
        mode = "dense-only"
    if args.use_rerank:
        mode += "+rerank"
    print(f"Running retrieval eval on {len(cases)} cases ({mode})...")
    for idx, case in enumerate(cases, 1):
        query = str(case.get("query", "")).strip()
        if not query:
            continue
        expected_terms = [str(t).lower() for t in case.get("expected_terms", [])]
        require_core_in_top_n = int(case.get("require_core_in_top_n", 0) or 0)
        require_faction = str(case.get("require_faction_in_top_n", "") or "").strip()
        nodes = retrieve_nodes(
            question=query,
            top_k=args.top_k,
            game_id=args.game,
            candidate_k=args.candidate_k,
            use_hybrid=not args.no_hybrid,
            use_rerank=args.use_rerank,
        )
        sources = nodes_to_sources(nodes[: args.top_k])
        hit, coverage = _score_case(sources, expected_terms)
        hits += int(hit)
        total_coverage += coverage
        top_source = sources[0]["source_label"] if sources else "-"
        ordering_ok = True
        if require_core_in_top_n > 0:
            ordering_checks += 1
            ordering_ok = ordering_ok and _has_core_in_top_n(sources, require_core_in_top_n)
            ordering_passes += int(ordering_ok)
        if require_faction:
            ordering_checks += 1
            ordering_ok = ordering_ok and _has_faction_in_top_n(
                sources, max(require_core_in_top_n, 3), require_faction
            )
            ordering_passes += int(ordering_ok)
        print(
            f"[{idx}] {'HIT' if hit else 'MISS'} "
            f"coverage={coverage:.2f} "
            f"core_top{require_core_in_top_n if require_core_in_top_n > 0 else '-'}="
            f"{'OK' if ordering_ok else 'MISS'} "
            f"query={query} "
            f"top_source={top_source}"
        )

    total = max(1, len(cases))
    recall_at_k = hits / total
    avg_coverage = total_coverage / total
    print("")
    print(f"Recall@{args.top_k}: {recall_at_k:.3f} ({hits}/{total})")
    print(f"Avg expected-term coverage: {avg_coverage:.3f}")
    if ordering_checks > 0:
        print(
            "Core-priority checks: "
            f"{ordering_passes}/{ordering_checks} "
            f"({ordering_passes / ordering_checks:.3f})"
        )


if __name__ == "__main__":
    main()
