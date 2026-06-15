"""Curated 'how to play' guides (Finnish) loaded from YAML."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import yaml

from src.settings import CURATED_DIR

HOW_TO_PLAY_DIR = CURATED_DIR / "how_to_play"

HOW_TO_PLAY_GAME_IDS = frozenset(
    {
        "sansibilia",
        "brambletrek",
        "brambletrek_2",
        "lighthouse",
        "apothecaria",
        "whispers",
        "colostle",
        "ashes",
        "outgunned",
        "tor",
        "coriolis",
        "cosmere",
        "mlp",
        "dnd5e",
    }
)


def _section_to_markdown(section: dict[str, Any]) -> str:
    heading = (section.get("heading") or "").strip()
    parts: list[str] = []
    if heading:
        parts.append(f"## {heading}")

    body = section.get("body")
    if isinstance(body, str) and body.strip():
        parts.append(body.strip())

    bullets = section.get("bullets")
    if isinstance(bullets, list) and bullets:
        parts.extend(f"- {str(item).strip()}" for item in bullets if str(item).strip())

    return "\n\n".join(parts)


def _compose_markdown(data: dict[str, Any]) -> str:
    sections = data.get("sections")
    if not isinstance(sections, list):
        return ""
    blocks = [_section_to_markdown(s) for s in sections if isinstance(s, dict)]
    return "\n\n".join(block for block in blocks if block)


@lru_cache(maxsize=32)
def load_how_to_play(game_id: str) -> dict[str, Any] | None:
    if game_id not in HOW_TO_PLAY_GAME_IDS:
        return None
    path = HOW_TO_PLAY_DIR / f"{game_id}.yaml"
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        return None
    return data


def how_to_play_markdown(game_id: str) -> str | None:
    data = load_how_to_play(game_id)
    if not data:
        return None
    return _compose_markdown(data)


def how_to_play_response(game_id: str) -> dict[str, Any] | None:
    data = load_how_to_play(game_id)
    if not data:
        return None
    markdown = _compose_markdown(data)
    sections = data.get("sections")
    return {
        "game_id": game_id,
        "title": data.get("title") or "Näin pelaat",
        "markdown": markdown,
        "sections": sections if isinstance(sections, list) else [],
    }
