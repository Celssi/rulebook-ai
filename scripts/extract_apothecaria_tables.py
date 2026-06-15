#!/usr/bin/env python3
"""Extract Apothecaria curated tables from the printer-friendly PDF into YAML."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
import yaml

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "docs/apothecaria/apothecaria-pages.pdf"
OUT = ROOT / "data/curated"

RANK_KEYS = {
    "A": "ace",
    "ACE": "ace",
    "1": "1",
    "2": "2",
    "3": "3",
    "4": "4",
    "5": "5",
    "6": "6",
    "7": "7",
    "8": "8",
    "9": "9",
    "10": "10",
    "J": "jack",
    "Q": "queen",
    "K": "king",
}

AILMENT_TIERS = {
    "Novice Ailments": "novice",
    "Intermediate Ailments": "intermediate",
    "Advanced Ailments": "advanced",
    "Expert Ailments": "expert",
}

LOCALE_HEADERS = {
    "Village": "village",
    "Glimmerwood Grove": "glimmerwood",
    "Blastfire Bog": "blastfire_bog",
    "Meltwater Loch": "meltwater_loch",
    "Dreamwater Depths": "dreamwater_depths",
    "Moonbreaker Mountain": "moonbreaker_mountain",
    "The Cloud Isles": "cloud_isles",
    "Hero's Hollow": "heros_hollow",
    "Hero’s Hollow": "heros_hollow",
    "The Strange": "the_strange",
}

TAG_RE = re.compile(r"\[([A-Z][A-Z ]*?)\s*\]")
RANK_LINE_RE = re.compile(
    r"^(?P<rank>(?:\d{1,2}|J|Q|K|A)|Queen/\s*King)\)\s*(?P<name>.+)$",
    re.IGNORECASE,
)
LOCALE_EVENT_RE = re.compile(
    r"^(?P<rank>A|\d{1,2}|J|Q|K)\s*$|^(?P<rank2>A|\d{1,2}|J|Q|K)\s+(?P<text>.+)$",
    re.IGNORECASE,
)


def normalize_rank(raw: str) -> str:
    raw = raw.strip().upper().replace(" ", "")
    if raw in ("QUEEN/KING", "QUEEN/K"):
        return "king"
    return RANK_KEYS.get(raw, raw.lower())


def parse_tags(text: str) -> list[str]:
    tags = []
    for m in TAG_RE.finditer(text):
        tag = m.group(1).strip()
        if tag:
            tags.append(tag)
    return tags


def parse_timer(text: str) -> int | None:
    m = re.search(r"Timer:\s*(\d+)", text, re.IGNORECASE)
    return int(m.group(1)) if m else None


def parse_potency(text: str) -> int:
    stars = text.count("★") + text.count("☆")
    if stars:
        return stars
    m = re.search(r"SWEET\s+(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    m = re.search(r"POISON\s+(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    tags = parse_tags(text)
    return max(1, len(tags)) if tags else 1


def extract_ailments(doc: fitz.Document) -> dict:
    tiers: dict[str, dict] = {t: {} for t in AILMENT_TIERS.values()}
    current_tier: str | None = None
    current_rank: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current_rank, buffer
        if not current_tier or not current_rank or not buffer:
            buffer = []
            return
        block = " ".join(buffer)
        block = re.sub(r"\s+", " ", block).strip()
        name_m = re.match(r"^(.+?)\s*[-–—]", block)
        name = name_m.group(1).strip() if name_m else block.split(" - ")[0].strip()
        cons_m = re.search(r"Consequence:\s*(.+?)(?:Extra:|$)", block, re.IGNORECASE)
        consequence = cons_m.group(1).strip() if cons_m else ""
        extra_m = re.search(r"Extra:\s*(.+)$", block, re.IGNORECASE)
        extra = extra_m.group(1).strip() if extra_m else ""
        entry = {
            "name": name,
            "tags": parse_tags(block),
            "timer": parse_timer(block),
            "potency": max(1, block.count("] [") + 1) if parse_tags(block) else 1,
            "description": block,
            "consequence": consequence,
        }
        if extra:
            entry["extra"] = extra
        if "Double Trouble" in name:
            entry["special"] = "draw_two_advanced"
        tiers[current_tier][current_rank] = entry
        buffer = []

    for page in doc:
        for line in page.get_text().splitlines():
            line = line.strip()
            if not line:
                continue
            for header, tier_id in AILMENT_TIERS.items():
                if header in line:
                    flush()
                    current_tier = tier_id
                    current_rank = None
                    break
            if line.endswith("Ailments") and line.split()[0] in ("Novice", "Intermediate", "Advanced", "Expert"):
                flush()
                current_tier = line.split()[0].lower()
                current_rank = None
                continue
            m = re.match(r"^(\d{1,2}|J|Q|K)\)\s*(.+)$", line, re.IGNORECASE)
            if m and current_tier:
                flush()
                current_rank = normalize_rank(m.group(1))
                buffer = [m.group(2).strip()]
                continue
            if re.match(r"^J\)\s", line, re.I):
                flush()
                current_rank = "jack"
                buffer = [line[2:].strip()]
                continue
            if current_rank and current_tier:
                if re.match(r"^\d{1,2}\)", line):
                    flush()
                    continue
                buffer.append(line)
    flush()
    return tiers


def extract_locale_events(doc: fitz.Document) -> dict:
    locales: dict[str, dict] = {}
    current_locale: str | None = None
    current_rank: str | None = None
    buffer: list[str] = []

    def flush() -> None:
        nonlocal current_rank, buffer
        if not current_locale or not current_rank:
            buffer = []
            return
        text = " ".join(buffer)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            locales.setdefault(current_locale, {})[current_rank] = text
        buffer = []

    lines_all: list[str] = []
    for page in doc:
        lines_all.extend(page.get_text().splitlines())

    i = 0
    while i < len(lines_all):
        line = lines_all[i].strip()
        i += 1
        if not line:
            continue
        matched_locale = None
        for header, loc_id in LOCALE_HEADERS.items():
            if line == header or (header in line and len(line) < len(header) + 5):
                matched_locale = loc_id
                break
        if matched_locale:
            flush()
            current_locale = matched_locale
            current_rank = None
            continue
        if not current_locale:
            continue
        if line.isdigit() and len(line) <= 2:
            flush()
            current_rank = normalize_rank(line)
            continue
        if line in ("A", "J", "Q", "K"):
            flush()
            current_rank = normalize_rank(line)
            continue
        if current_rank:
            if line in LOCALE_HEADERS or any(h in line for h in LOCALE_HEADERS):
                flush()
                current_locale = None
                current_rank = None
                i -= 1
                continue
            buffer.append(line)
    flush()
    return locales


def extract_familiars(doc: fitz.Document) -> tuple[dict, dict]:
    text = "\n".join(page.get_text() for page in doc)
    type_block = re.search(
        r"you may draw randomly\s+from the choices below\..*?The Calling Ritual",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    skill_block = re.search(
        r"check the list below\.\s*(.*?Familiars aren.t just good company)",
        text,
        re.DOTALL,
    )
    types: dict[str, str] = {}
    skills: dict[str, str] = {}

    def parse_rank_table(block: str) -> dict[str, str]:
        out: dict[str, str] = {}
        current_rank: str | None = None
        parts = re.split(r"\n(Ace|Seven|Two|Eight|Three|Nine|Four|Ten|Five|Jack|Six|Queen/\s*King)\n", block)
        if len(parts) < 2:
            return out
        for j in range(1, len(parts), 2):
            rank_raw = parts[j].strip()
            body = parts[j + 1] if j + 1 < len(parts) else ""
            rank = normalize_rank(rank_raw.split("/")[0])
            if rank_raw.lower().startswith("queen"):
                out["queen"] = body.strip().split("\n")[0].strip()
                out["king"] = body.strip().split("\n")[0].strip()
            else:
                out[rank] = re.sub(r"\s+", " ", body).strip()
        return out

    if type_block:
        types = parse_rank_table(type_block.group(0))
    if skill_block:
        skills = parse_rank_table(skill_block.group(1))
    return types, skills


def extract_patient_types() -> dict:
    return {
        "hearts": "Villager",
        "diamonds": "Adventurer",
        "clubs": "Monster",
        "spades": "Repeat patient",
    }


def extract_reagents(doc: fitz.Document) -> list[dict]:
    """Best-effort reagent extraction from reagent pages."""
    reagents: list[dict] = []
    text = "\n".join(page.get_text() for page in doc[20:30])
    chunks = re.split(r"\n(?=[A-Z][^\n]{2,40}\n-\s*(?:PLANT|ANIMAL|MAGIC))", text)
    for chunk in chunks:
        lines = [ln.strip() for ln in chunk.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        name = lines[0]
        if name in ("Reagents Explanation", "Forest Reagents", "Loch Reagents", "Mountain Reagents", "Dungeon Reagents"):
            continue
        header = next((ln for ln in lines[1:4] if ln.startswith("-")), "")
        if not header:
            continue
        type_m = re.search(r"-\s*(PLANT|ANIMAL|MAGIC)\s*-", header)
        locales_m = re.findall(r"(Forest|Loch|Mountain|Dungeon|Bog|Isles|Strange|Village|Depths)\s*\((\d+)\)", header)
        entry: dict = {
            "name": name,
            "type": type_m.group(1) if type_m else "",
            "locales": {loc.lower().replace(" ", "_"): int(val) for loc, val in locales_m},
            "header": header,
            "body": " ".join(lines[2:]),
        }
        entry["tags"] = parse_tags(entry["body"])
        if "Requires a WAND" in entry["body"] or "Requires a Wand" in entry["body"]:
            entry["requires_wand"] = True
        reagents.append(entry)
    return reagents


def main() -> int:
    if not PDF.exists():
        print(f"Missing PDF: {PDF}", file=sys.stderr)
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(PDF)

    ailments = extract_ailments(doc)
    with open(OUT / "apothecaria_ailments.yaml", "w") as f:
        f.write("# Ailments by reputation tier — Apothecaria p.12–19\n")
        yaml.dump({"tiers": ailments}, f, allow_unicode=True, sort_keys=False, width=120)

    locales = extract_locale_events(doc)
    with open(OUT / "apothecaria_locale_events.yaml", "w") as f:
        f.write("# Locale foraging events — Apothecaria p.34–51\n")
        yaml.dump({"locales": locales}, f, allow_unicode=True, sort_keys=False, width=120)

    fam_types, fam_skills = extract_familiars(doc)
    with open(OUT / "apothecaria_familiars.yaml", "w") as f:
        f.write("# Familiar type + skill — Apothecaria p.10–11\n")
        yaml.dump({"types": fam_types, "skills": fam_skills}, f, allow_unicode=True, sort_keys=False, width=120)

    with open(OUT / "apothecaria_patient_types.yaml", "w") as f:
        f.write("# Patient type by suit — Apothecaria p.5\n")
        yaml.dump({"suits": extract_patient_types()}, f, allow_unicode=True, sort_keys=False)

    reagents = extract_reagents(doc)
    with open(OUT / "apothecaria_reagents.yaml", "w") as f:
        f.write("# Reagents — Apothecaria p.20–29 (verify against PDF)\n")
        yaml.dump({"reagents": reagents}, f, allow_unicode=True, sort_keys=False, width=120)

    print(f"Wrote {len(ailments)} ailment tiers, {len(locales)} locales, {len(reagents)} reagents")
    for tier, rows in ailments.items():
        print(f"  {tier}: {len(rows)} ailments")
    for loc, rows in locales.items():
        print(f"  {loc}: {len(rows)} events")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
