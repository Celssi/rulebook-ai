"""Shared text cleaning for ingest and OCR."""

from __future__ import annotations

import re


def clean_text(text: str) -> str:
    text = text.replace("\x00", "")
    # Join words split across line breaks in PDF/OCR output.
    text = re.sub(r"([A-Za-z])-\n([A-Za-z])", r"\1\2", text)
    # Collapse noisy whitespace while preserving paragraph boundaries.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" ?\n ?", "\n", text)
    return text.strip()


def is_meaningful(
    text: str,
    min_chars: int = 40,
    min_alpha_ratio: float = 0.25,
) -> bool:
    stripped = re.sub(r"[\s™\n]+", "", text)
    if len(stripped) < min_chars:
        return False
    alpha = sum(1 for c in stripped if c.isalpha())
    ratio = alpha / max(1, len(stripped))
    return ratio >= min_alpha_ratio
