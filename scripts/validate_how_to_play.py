#!/usr/bin/env python3
"""Validate curated how-to-play YAML guides."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import importlib.util

_how_to_play_path = ROOT / "src" / "games" / "how_to_play.py"
_spec = importlib.util.spec_from_file_location("how_to_play", _how_to_play_path)
assert _spec and _spec.loader
_how_to_play = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_how_to_play)

HOW_TO_PLAY_DIR = _how_to_play.HOW_TO_PLAY_DIR
HOW_TO_PLAY_GAME_IDS = _how_to_play.HOW_TO_PLAY_GAME_IDS
how_to_play_markdown = _how_to_play.how_to_play_markdown
load_how_to_play = _how_to_play.load_how_to_play

FORBIDDEN_IDS = frozenset({"40k"})

MIN_SOURCE_PAGES = 3
MIN_MARKDOWN_LEN = 200

# Each game must mention these substrings somewhere in the composed guide.
GAME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "sansibilia": ("Day", "kaupungin"),
    "brambletrek": ("Legacy", "Journey"),
    "lighthouse": ("logbook", "valo"),
    "apothecaria": ("foraging", "maine"),
    "whispers": ("Hollows", "Whispers"),
    "colostle": ("exploration", "Combat"),
    "ashes": ("Sanctuary", "Ember"),
}


def _section_headings(sections: list) -> list[str]:
    headings: list[str] = []
    if not isinstance(sections, list):
        return headings
    for section in sections:
        if isinstance(section, dict):
            heading = section.get("heading")
            if isinstance(heading, str) and heading.strip():
                headings.append(heading.strip())
    return headings


def _validate_file(game_id: str) -> list[str]:
    errors: list[str] = []
    data = load_how_to_play(game_id)
    if data is None:
        return [f"{game_id}: missing or invalid YAML"]

    if data.get("game_id") != game_id:
        errors.append(f"{game_id}: game_id field must match filename")

    title = data.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append(f"{game_id}: missing title")

    source = data.get("source")
    if not isinstance(source, dict):
        errors.append(f"{game_id}: missing source")
    else:
        pdf = source.get("pdf")
        pages = source.get("pages")
        if not isinstance(pdf, str) or not pdf.strip():
            errors.append(f"{game_id}: source.pdf required")
        if not isinstance(pages, list) or len(pages) < MIN_SOURCE_PAGES:
            errors.append(
                f"{game_id}: source.pages must be a list with at least {MIN_SOURCE_PAGES} entries"
            )

    sections = data.get("sections")
    if not isinstance(sections, list) or len(sections) < 3:
        errors.append(f"{game_id}: need at least 3 sections")
    elif isinstance(sections, list):
        headings = _section_headings(sections)
        headings_lower = [h.lower() for h in headings]

        if not any("tarvitset" in h for h in headings_lower):
            errors.append(f"{game_id}: missing section heading containing 'Tarvitset'")
        if not any("sovelluksessa" in h for h in headings_lower):
            errors.append(f"{game_id}: missing 'Sovelluksessa' section")

        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                errors.append(f"{game_id}: section {i} must be a mapping")
                continue
            heading = section.get("heading")
            body = section.get("body")
            bullets = section.get("bullets")
            has_body = isinstance(body, str) and body.strip()
            has_bullets = isinstance(bullets, list) and any(str(b).strip() for b in bullets)
            if not isinstance(heading, str) or not heading.strip():
                errors.append(f"{game_id}: section {i} missing heading")
            if not has_body and not has_bullets:
                errors.append(f"{game_id}: section {i} needs body or bullets")

    md = how_to_play_markdown(game_id)
    if not md or len(md) < MIN_MARKDOWN_LEN:
        errors.append(f"{game_id}: markdown output too short")

    if md:
        md_lower = md.lower()
        for keyword in GAME_KEYWORDS.get(game_id, ()):
            if keyword.lower() not in md_lower:
                errors.append(f"{game_id}: missing expected keyword '{keyword}' in guide text")

    return errors


def main() -> int:
    errors: list[str] = []

    if not HOW_TO_PLAY_DIR.is_dir():
        print(f"FAIL: missing directory {HOW_TO_PLAY_DIR}")
        return 1

    yaml_files = {p.stem for p in HOW_TO_PLAY_DIR.glob("*.yaml")}
    missing = HOW_TO_PLAY_GAME_IDS - yaml_files
    extra = yaml_files - HOW_TO_PLAY_GAME_IDS
    forbidden = yaml_files & FORBIDDEN_IDS

    if missing:
        errors.append(f"missing YAML for: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected YAML files: {', '.join(sorted(extra))}")
    if forbidden:
        errors.append(f"forbidden how-to-play for: {', '.join(sorted(forbidden))}")

    for game_id in sorted(HOW_TO_PLAY_GAME_IDS):
        errors.extend(_validate_file(game_id))

    if errors:
        print("validate_how_to_play: FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"validate_how_to_play: OK ({len(HOW_TO_PLAY_GAME_IDS)} games)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
