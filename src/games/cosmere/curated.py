"""Cosmere plot dice curated table."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR

_PLOT_DICE_PATH = CURATED_DIR / "cosmere_plot_dice.yaml"


@lru_cache(maxsize=1)
def _load_plot_dice() -> dict[str, Any]:
    with _PLOT_DICE_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("faces") or {}


def lookup_plot_face(face: int) -> dict[str, str]:
    faces = _load_plot_dice()
    entry = faces.get(str(face)) or faces.get(str(int(face)))
    if not isinstance(entry, dict):
        return {"label": "neutral", "text": ""}
    return {
        "label": str(entry.get("label", "neutral")),
        "text": str(entry.get("text", "")),
    }


def format_plot_dice_roll(rolls: list[int]) -> str:
    lines = ["**Plot dice:**", ""]
    for roll in rolls:
        face = lookup_plot_face(roll)
        label = face["label"]
        text = face["text"]
        if label in ("complication", "opportunity"):
            lines.append(f"- **{roll}** — **{label.title()}**: {text}")
        else:
            lines.append(f"- **{roll}** — {text or 'neutral'}")
    return "\n".join(lines)


def all_faces_valid() -> bool:
    faces = _load_plot_dice()
    for key in ("1", "6"):
        entry = faces.get(key)
        if not isinstance(entry, dict):
            return False
        label = str(entry.get("label", ""))
        if key == "1" and label != "complication":
            return False
        if key == "6" and label != "opportunity":
            return False
    return True
