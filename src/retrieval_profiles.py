"""Retrieval profile configuration (shared by API and domain layers)."""

from __future__ import annotations

RETRIEVAL_PROFILES = {
    "Fast": {"candidate_k": 14, "use_hybrid": False, "use_rerank": False},
    "Balanced": {"candidate_k": 24, "use_hybrid": True, "use_rerank": False},
    "Quality": {"candidate_k": 70, "use_hybrid": True, "use_rerank": False},
    "Quality+ rerank": {"candidate_k": 70, "use_hybrid": True, "use_rerank": True},
}

# Balanced (hybrid dense + lexical) is a much better default than Fast (dense-only,
# small candidate pool). Quality / Quality+ rerank remain opt-in for best recall.
DEFAULT_RETRIEVAL_PROFILE = "Balanced"


def resolve_retrieval_profile(name: str | None) -> tuple[str, dict]:
    """Return a valid profile name and config, falling back to Fast."""
    if name in RETRIEVAL_PROFILES:
        return name, RETRIEVAL_PROFILES[name]
    return DEFAULT_RETRIEVAL_PROFILE, RETRIEVAL_PROFILES[DEFAULT_RETRIEVAL_PROFILE]
