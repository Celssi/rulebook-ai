#!/usr/bin/env python3
"""One-shot: extract Whispers in the Walls tables from PDF into curated YAML."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import fitz
import yaml

ROOT = Path(__file__).resolve().parent.parent
PDF = ROOT / "docs/whispers/Whispers In the Walls 2e - Pages.pdf"
OUT = ROOT / "data/curated"

_RANK_MAP = {
    "A": "ace",
    "J": "jack",
    "Q": "queen",
    "K": "king",
    **{str(n): str(n) for n in range(2, 11)},
}
_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")
_RANK_RE = r"(?:A|[2-9]|10|J|Q|K)"


def _page_text(doc: fitz.Document, page_num: int) -> str:
    return doc[page_num - 1].get_text()


def _strip_noise(text: str) -> str:
    drop = re.compile(
        r"^(LOCATIONS|HEARTS|DIAMONDS|CLUBS|SPADES|JOKERS|THE ENDING|"
        r"THE FIRST|THE SECOND|ALL JOKERS|JOKER|Anguishing|Creaking|Trampled|"
        r"The roofs|The Hollows|anguish hopelessness|Peace Hope).*$",
        re.MULTILINE,
    )
    text = drop.sub("", text)
    # PDF page numbers before section headers (not card ranks)
    text = re.sub(
        r"\n\d{1,2}\n(?:LOCATIONS|HEARTS|DIAMONDS|CLUBS|SPADES|THE ENDING|JOKERS)\n",
        "\n",
        text,
    )
    return text


def _parse_rank_blocks(text: str, *, has_title: bool = False) -> dict[str, dict[str, str]]:
    text = _strip_noise(text)
    parts = re.split(rf"\n({_RANK_RE})\n", text)
    out: dict[str, dict[str, str]] = {}
    i = 1
    while i < len(parts) - 1:
        rank_raw = parts[i].strip()
        body = parts[i + 1].strip()
        i += 2
        rank_key = _RANK_MAP.get(rank_raw, rank_raw.lower())
        if not body:
            continue
        entry: dict[str, str] = {"body": body}
        if has_title and "|" in body.split("\n", 1)[0]:
            title_line, _, rest = body.partition("\n")
            title, _, narrative = title_line.partition("|")
            entry["title"] = title.strip()
            entry["body"] = (narrative.strip() + ("\n" + rest if rest else "")).strip()
        if rank_key in out and out[rank_key].get("body"):
            continue
        out[rank_key] = entry
    return out


def _write_yaml(name: str, data: dict) -> None:
    path = OUT / name
    header = f"# {name} — Whispers in the Walls 2e (ORC); verify against docs/whispers PDF\n"
    with path.open("w", encoding="utf-8") as f:
        f.write(header)
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False, width=100)


def main() -> int:
    if not PDF.exists():
        print(f"Missing PDF: {PDF}", file=sys.stderr)
        return 1
    doc = fitz.open(PDF)

    locations = _parse_rank_blocks(
        _page_text(doc, 9) + "\n" + _page_text(doc, 10) + "\n" + _page_text(doc, 11),
        has_title=True,
    )
    # Remove duplicate joker location entry parsed as rank if any
    if "jack" in locations and locations["jack"].get("title") == "Sailboat":
        pass  # keep J/Q/K from page 11

    joker_loc_text = _page_text(doc, 11)
    jm = re.search(r"JOKER\s*\n(.+?)(?=\n\d+\s*\n|$)", joker_loc_text, re.DOTALL)
    if jm:
        body = jm.group(1).strip()
        if "|" in body:
            title, _, narrative = body.partition("|")
            locations["joker"] = {"title": title.strip(), "body": narrative.strip()}
        else:
            locations["joker"] = {"title": "Sunken Leviathan", "body": body}

    hearts = _parse_rank_blocks(_page_text(doc, 13) + "\n" + _page_text(doc, 14) + "\n" + _page_text(doc, 15))
    diamonds = _parse_rank_blocks(_page_text(doc, 17) + "\n" + _page_text(doc, 18) + "\n" + _page_text(doc, 19))
    clubs = _parse_rank_blocks(_page_text(doc, 21) + "\n" + _page_text(doc, 22) + "\n" + _page_text(doc, 23))
    spades = _parse_rank_blocks(_page_text(doc, 25) + "\n" + _page_text(doc, 26) + "\n" + _page_text(doc, 27))

    joker_text = _page_text(doc, 29)
    first_m = re.search(r"THE FIRST\s*\n(.+?)(?=THE SECOND)", joker_text, re.DOTALL)
    second_m = re.search(r"THE SECOND\s*\n(.+?)(?=ALL JOKERS)", joker_text, re.DOTALL)
    all_m = re.search(r"ALL JOKERS REVEALED\s*\n(.+)$", joker_text, re.DOTALL)
    jokers = {
        "first": {"body": first_m.group(1).strip() if first_m else ""},
        "second": {"body": second_m.group(1).strip() if second_m else ""},
        "all_revealed": {"body": all_m.group(1).strip() if all_m else ""},
    }

    endings = _parse_rank_blocks(_page_text(doc, 31) + "\n" + _page_text(doc, 32) + "\n" + _page_text(doc, 33))
    end_joker = _page_text(doc, 33)
    jm2 = re.search(r"JOKER\s*\n(.+?)(?=INVESTIGATION|$)", end_joker, re.DOTALL)
    if jm2:
        endings["joker"] = {"body": jm2.group(1).strip()}

    oracle = {
        "2-3": "The answer is no, and…",
        "4-6": "The answer is no.",
        "7": "The answer is yes, but…",
        "8-10": "The answer is yes.",
        "11-12": "The answer is yes, and…",
    }

    _write_yaml("whispers_locations.yaml", {"ranks": locations})
    _write_yaml("whispers_hearts.yaml", {"ranks": hearts})
    _write_yaml("whispers_diamonds.yaml", {"ranks": diamonds})
    _write_yaml("whispers_clubs.yaml", {"ranks": clubs})
    _write_yaml("whispers_spades.yaml", {"ranks": spades})
    _write_yaml("whispers_jokers.yaml", jokers)
    _write_yaml("whispers_endings.yaml", {"ranks": endings})
    _write_yaml("whispers_oracle.yaml", {"bands": oracle})

    missing = []
    for table_name, ranks in [
        ("locations", locations),
        ("hearts", hearts),
        ("diamonds", diamonds),
        ("clubs", clubs),
        ("spades", spades),
        ("endings", endings),
    ]:
        for r in _ALL_RANKS:
            if r not in ranks:
                missing.append(f"{table_name}:{r}")

    if missing:
        print("WARNING missing ranks:", ", ".join(missing))
    else:
        print("All standard ranks present in each table.")
    print(f"Wrote curated YAML to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
