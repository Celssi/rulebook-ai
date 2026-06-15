#!/usr/bin/env python3
"""Extract Brambletrek 2 curated data from the core PDF.

Usage:
  python3 scripts/extract_brambletrek_2_pdf.py              # write JSON extract
  python3 scripts/extract_brambletrek_2_pdf.py --write-yaml # refresh curated YAML
  python3 scripts/extract_brambletrek_2_pdf.py --check      # diff YAML vs PDF
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
PDF_PATH = ROOT / "docs/brambletrek_2/Brambletrek_2_-_Tales_in_the_Hundred_Acre_Woods.pdf"
CURATED = ROOT / "data/curated"
EXTRACT_JSON = CURATED / "_bt2_extract.json"

LEGACY_PAGE_MAP: dict[int, str] = {
    18: "bramble",
    19: "pooh",
    20: "piglet",
    21: "eeyore",
    22: "tigger",
    23: "owl",
    24: "rabbit",
    25: "kanga_roo",
    26: "salvager",
    27: "snoozer",
    28: "shadowcaster",
    29: "smasher",
    30: "singer",
    31: "snickerer",
    32: "solver",
    33: "sleeptalker",
}

LEGACY_LABELS: dict[str, str] = {
    "bramble": "Bramble",
    "pooh": "Winnie the Pooh",
    "piglet": "Piglet",
    "eeyore": "Eeyore",
    "tigger": "Tigger",
    "owl": "Owl",
    "rabbit": "Rabbit",
    "kanga_roo": "Kanga & Roo",
    "salvager": "Salvager",
    "snoozer": "Snoozer",
    "shadowcaster": "Shadowcaster",
    "smasher": "Smasher",
    "singer": "Singer",
    "snickerer": "Snickerer",
    "solver": "Solver",
    "sleeptalker": "Sleeptalker",
}

RANK_KEYS = ("2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king", "ace")
RANK_RE = r"(?:2|3|4|5|6|7|8|9|10|JACK|QUEEN|KING|ACE)"
SUITS = ("hearts", "diamonds", "spades", "clubs")

TACTIC_PAGE_PAIRS: list[tuple[int, str, str]] = [
    (52, "bramble", "pooh"),
    (53, "piglet", "eeyore"),
    (54, "tigger", "owl"),
    (55, "rabbit", "kanga_roo"),
    (56, "snoozer", "salvager"),
    (57, "smasher", "shadowcaster"),
    (58, "singer", "snickerer"),
    (59, "solver", "sleeptalker"),
]

OPPONENT_PAGES: dict[str, int] = {
    "bumblebeast": 61,
    "heffalump": 63,
    "jagular": 65,
    "rockodile": 67,
    "snuffalo": 69,
    "woozle": 71,
    "tootle": 73,
    "totter": 75,
    "lizzle": 77,
    "lumpus": 79,
    "grizzle": 81,
    "spookle": 83,
}


def _humanize_label(name: str) -> str:
    name = name.replace("\u2019", "'").strip().title()
    return name.replace("'S", "'s")


def _slug(text: str) -> str:
    text = text.lower().replace("'", "")
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


def _clean_pdf_text(text: str) -> str:
    text = re.sub(r"Lauri Mukkala \(Order #\d+\)", "", text)
    text = re.sub(r"\r\n", "\n", text)
    return text


def _open_doc():
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("PyMuPDF (fitz) required") from exc
    return fitz.open(str(PDF_PATH))


def _page_text(doc, page_num: int) -> str:
    return _clean_pdf_text(doc[page_num - 1].get_text())


def _parse_spread(line: str) -> tuple[int, int, int]:
    h = re.search(r"(\d+)\s*HEALTH", line, re.I)
    s = re.search(r"(\d+)\s*SUPPLIES", line, re.I)
    m = re.search(r"(\d+)\s*MORALE", line, re.I)
    if not (h and s and m):
        raise ValueError(f"Cannot parse spread: {line!r}")
    return int(h.group(1)), int(s.group(1)), int(m.group(1))


def _legacy_name_match(leg_id: str, line: str) -> bool:
    upper = line.upper().strip()
    label = LEGACY_LABELS[leg_id].upper()
    if upper == label:
        return True
    if leg_id == "pooh" and upper == "WINNIE THE POOH":
        return True
    if leg_id == "kanga_roo" and upper == "KANGA & ROO":
        return True
    return False


def extract_legacies(doc) -> dict[str, Any]:
    legacies: dict[str, Any] = {}
    for page, leg_id in LEGACY_PAGE_MAP.items():
        text = _page_text(doc, page)
        lines = [
            ln.strip()
            for ln in text.splitlines()
            if ln.strip() and not re.fullmatch(r"\d+", ln.strip())
        ]
        spread_line = next(
            ln for ln in lines if "HEALTH" in ln and "SUPPLIES" in ln
        )
        health, supplies, morale = _parse_spread(spread_line)
        name_idx = next(i for i, ln in enumerate(lines) if _legacy_name_match(leg_id, ln))
        tagline = lines[name_idx - 1] if name_idx > 0 else ""
        post = text.split("RESOURCE SPREAD", 1)[-1]
        if "|" in post:
            post = post.split("|", 1)[1]
        abilities: list[dict[str, str]] = []
        for m in re.finditer(
            r"([A-Z][A-Z'\u2019&\s]+?):\s*((?:ONCE|IF|WHEN|THE|DURING|A).+?)"
            r"(?=\n[A-Z][A-Z'\u2019&\s]+?:\s*(?:ONCE|IF|WHEN|THE|DURING|A)|\Z)",
            post,
            re.S,
        ):
            label = _humanize_label(m.group(1))
            description = re.sub(r"\s+", " ", m.group(2).strip()).rstrip(".") + "."
            abilities.append(
                {
                    "id": _slug(label),
                    "label": label,
                    "description": description,
                }
            )
        legacies[leg_id] = {
            "label": LEGACY_LABELS[leg_id],
            "tagline": tagline,
            "health": health,
            "supplies": supplies,
            "morale": morale,
            "abilities": abilities,
        }
    return legacies


def extract_arrival(doc) -> dict[str, str]:
    text = _page_text(doc, 17)
    bands: dict[str, str] = {}
    patterns = [
        ("ace", r"Ace\s+(.*?)(?=\n2-4|\Z)"),
        ("2-4", r"2-4\s+(.*?)(?=\n5-7|\Z)"),
        ("5-7", r"5-7\s+(.*?)(?=\n8-10|\Z)"),
        ("8-10", r"8-10\s+(.*?)(?=\nJack|\Z)"),
        ("jack", r"Jack\s+(.*?)(?=\nQueen|\Z)"),
        ("queen", r"Queen\s+(.*?)(?=\nKing|\Z)"),
        ("king", r"King\s+(.*?)(?=\nLauri|\Z)"),
    ]
    for band, pat in patterns:
        m = re.search(pat, text, re.S | re.I)
        if not m:
            continue
        body = re.sub(r"\s+", " ", m.group(1).strip())
        bands[band] = body
    return bands


def _rank_key(token: str) -> str:
    t = token.strip().lower()
    if t == "jack":
        return "jack"
    if t == "queen":
        return "queen"
    if t == "king":
        return "king"
    if t == "ace":
        return "ace"
    return t


def _parse_event_mechanics(text: str) -> dict[str, Any]:
    row: dict[str, Any] = {}
    tags: list[str] = []
    label = text
    paren_blocks = re.findall(r"\([^)]+\)", text)
    for block in paren_blocks:
        label = label.replace(block, "").strip()
        inner = block.strip("()").strip()
        low = inner.lower()
        if low.startswith("combat"):
            row["combat"] = True
            tags.append("combat")
        elif "item" in low and "memory" not in low:
            tags.append("item")
        elif "hollow" in low:
            tags.append("hollow")
        elif "exit" in low:
            tags.append("exit")
        elif "gain" in low and "memory" in low:
            m = re.search(r"(\d+)", inner)
            if m:
                row["memory_fragments"] = int(m.group(1))
            tags.append("memory_fragment")
        elif "lose" in low and "health" in low:
            m = re.search(r"(\d+)", inner)
            if m:
                row["health"] = -int(m.group(1))
        elif "recover" in low and "health" in low:
            m = re.search(r"(\d+)", inner)
            if m:
                row["health"] = int(m.group(1))
        elif re.search(r"[+\-]\d+\s+all stats", low):
            m = re.search(r"([+\-]?\d+)", inner)
            if m:
                row["all_stats"] = int(m.group(1))
        elif "health" in low and "morale" in low and "suppl" in low:
            m = re.search(r"(\d+)", inner)
            if m:
                v = int(m.group(1))
                sign = -1 if inner.strip().startswith("-") else 1
                row["health"] = sign * v
                row["morale"] = sign * v
                row["supplies"] = sign * v
        else:
            for stat in ("health", "morale", "supplies"):
                m = re.search(rf"([+\-]?)(\d+)\s+{stat}", low)
                if m:
                    sign = -1 if m.group(1) == "-" else 1
                    row[stat] = sign * int(m.group(2))
    label = re.sub(r"\s+", " ", label).strip().rstrip(".")
    row["label"] = label
    if tags:
        row["tags"] = sorted(set(tags))
    return row


def _parse_rank_rows(body: str) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    body = "\n" + body.strip()
    parts = re.split(r"\n(2|3|4|5|6|7|8|9|10|JACK|QUEEN|KING|ACE)\n", body, flags=re.I)
    i = 1
    while i < len(parts) - 1:
        rank = _rank_key(parts[i])
        chunk = parts[i + 1]
        chunk = re.split(
            r"\n(?:DIAMONDS|SPADES|CLUBS|HEARTS|CARD\s|HALLOW)\b",
            chunk,
            maxsplit=1,
            flags=re.I,
        )[0]
        text = re.sub(r"\s+", " ", chunk.strip())
        if text:
            rows[rank] = _parse_event_mechanics(text)
        i += 2
    return rows


def _parse_suit_table(text: str, suit_marker: str) -> dict[str, dict[str, Any]]:
    m = re.search(rf"{suit_marker}\s*(?:[♥♦♠♣])?\s*(.*)", text, re.S | re.I)
    if not m:
        return {}
    return _parse_rank_rows(m.group(1))


def extract_exploration(doc) -> dict[str, dict[str, dict[str, Any]]]:
    pages = {35: "hearts", 36: "diamonds", 37: "spades", 38: "clubs"}
    markers = {
        "hearts": r"HEARTS",
        "diamonds": r"DIAMONDS",
        "spades": r"SPADES",
        "clubs": r"CLUBS",
    }
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for page, suit in pages.items():
        text = _page_text(doc, page)
        out[suit] = _parse_suit_table(text, markers[suit])
    return out


def extract_hollow(doc) -> dict[str, dict[str, dict[str, Any]]]:
    pages = {45: "hearts", 46: "diamonds", 47: "spades", 48: "clubs"}
    markers = {
        "hearts": r"HEARTS",
        "diamonds": r"DIAMONDS",
        "spades": r"SPADES",
        "clubs": r"CLUBS",
    }
    out: dict[str, dict[str, dict[str, Any]]] = {}
    for page, suit in pages.items():
        text = _page_text(doc, page)
        out[suit] = _parse_suit_table(text, markers[suit])
    return out


def extract_items(doc) -> dict[str, dict[str, str]]:
    text = _page_text(doc, 39).split("ITEMS", 1)[-1]
    rows = _parse_rank_rows(text)
    items: dict[str, dict[str, str]] = {}
    for rank, row in rows.items():
        label = row.get("label", "")
        if not label:
            continue
        if ". " in label:
            short, rest = label.split(". ", 1)
            items[rank] = {"label": short.strip(), "effect": f"{short.strip()}. {rest.strip()}"}
        else:
            items[rank] = {"label": label, "effect": label}
    return items


def _split_tactic_pair(chunk: str) -> tuple[str, str]:
    chunk = re.sub(r"\s+", " ", chunk.strip())
    matches = list(re.finditer(r"([A-Z][A-Za-z'\u2019\s]+):\s", chunk))
    if len(matches) >= 2:
        split_at = matches[1].start()
        return chunk[:split_at].strip(), chunk[split_at:].strip()
    return chunk, ""


def _split_tactic_reward(chunk: str) -> tuple[str, str]:
    chunk = re.sub(r"\s+", " ", chunk.strip())
    m = re.search(r"\.\s+([A-Z][A-Za-z'\u2019][A-Za-z'\u2019\s]*)\.\s+", chunk)
    if m:
        split_at = m.start() + 1
        return chunk[:split_at].strip(), chunk[split_at + 1 :].strip()
    return chunk, ""


def _parse_two_column_rank_table(text: str) -> tuple[dict[str, str], dict[str, str]]:
    left: dict[str, str] = {}
    right: dict[str, str] = {}
    text = "\n" + text.strip()
    parts = re.split(r"\n(2|3|4|5|6|7|8|9|10|JACK|QUEEN|KING|ACE)\n", text, flags=re.I)
    i = 1
    while i < len(parts) - 1:
        rank = _rank_key(parts[i])
        col_a, col_b = _split_tactic_pair(parts[i + 1])
        if col_a:
            left[rank] = re.sub(r"\s+", " ", col_a.strip())
        if col_b:
            right[rank] = re.sub(r"\s+", " ", col_b.strip())
        i += 2
    return left, right


def _parse_opponent_rank_table(text: str) -> tuple[dict[str, str], dict[str, str]]:
    tactics: dict[str, str] = {}
    rewards: dict[str, str] = {}
    text = "\n" + text.strip()
    parts = re.split(r"\n(2|3|4|5|6|7|8|9|10|JACK|QUEEN|KING|ACE)\n", text, flags=re.I)
    i = 1
    while i < len(parts) - 1:
        rank = _rank_key(parts[i])
        tac, rew = _split_tactic_reward(parts[i + 1])
        if tac:
            tactics[rank] = re.sub(r"\s+", " ", tac.strip())
        if rew:
            rewards[rank] = re.sub(r"\s+", " ", rew.strip())
        i += 2
    return tactics, rewards


def extract_player_tactics(doc) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {
        lid: {} for _page, left, right in TACTIC_PAGE_PAIRS for lid in (left, right)
    }
    for page, left_id, right_id in TACTIC_PAGE_PAIRS:
        text = _page_text(doc, page)
        body = re.split(r"\n2\n", text, maxsplit=1, flags=re.I)
        if len(body) < 2:
            continue
        left_rows, right_rows = _parse_two_column_rank_table("2\n" + body[1])
        out[left_id].update(left_rows)
        out[right_id].update(right_rows)
    return out


def extract_hollow_entry_exit(doc) -> tuple[dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    entry_rows = _parse_rank_rows(_page_text(doc, 44).split("HALLOW ENTRY PROMPTS", 1)[-1])
    entry = {rk: {"label": row["label"]} for rk, row in entry_rows.items() if row.get("label")}
    exit_rows = _parse_rank_rows(_page_text(doc, 49).split("HALLOW EXIT PROMPTS", 1)[-1])
    exit_out = {rk: {"label": row["label"]} for rk, row in exit_rows.items() if row.get("label")}
    return entry, exit_out


def extract_opponent_tactics(doc) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for opp_id, page in OPPONENT_PAGES.items():
        text = _page_text(doc, page)
        body = text.split("COMBAT TACTICS", 1)[-1]
        body = re.split(r"\n2\n", body, maxsplit=1, flags=re.I)
        if len(body) < 2:
            continue
        tactics, rewards = _parse_opponent_rank_table("2\n" + body[1])
        out[opp_id] = {"tactics": tactics, "reward_items": rewards}
    return out


def extract_all(doc) -> dict[str, Any]:
    return {
        "legacies": extract_legacies(doc),
        "arrival": extract_arrival(doc),
        "exploration": extract_exploration(doc),
        "hollow": extract_hollow(doc),
        "items": extract_items(doc),
        "player_tactics": extract_player_tactics(doc),
        "hollow_entry": extract_hollow_entry_exit(doc)[0],
        "hollow_exit": extract_hollow_entry_exit(doc)[1],
        "opponent_tactics": extract_opponent_tactics(doc),
    }


def _yaml_dump(data: Any) -> str:
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=1000,
        default_flow_style=False,
    )


def write_legacies_yaml(data: dict[str, Any]) -> None:
    legacies = data["legacies"]
    doc = {
        "overcome_the_odds": {
            "label": "Overcome the Odds",
            "description": (
                "Once per day, in place of one Legacy ability: draw Ability + Outcome "
                "vs an Unfortunate Event (Clubs/Spades) or in combat. Higher ability wins."
            ),
        },
        "legacies": legacies,
    }
    path = CURATED / "brambletrek_2_legacies.yaml"
    path.write_text("# Legacies (BT2 pp. 18-33).\n" + _yaml_dump(doc), encoding="utf-8")


def write_arrival_yaml(data: dict[str, Any]) -> None:
    bands = {k: {"label": v} for k, v in data["arrival"].items()}
    doc = {"bands": bands}
    path = CURATED / "brambletrek_2_how_did_i_get_here.yaml"
    path.write_text("# How did I get here? (BT2 p. 17).\n" + _yaml_dump(doc), encoding="utf-8")


def write_exploration_yaml(data: dict[str, Any]) -> None:
    path = CURATED / "brambletrek_2_exploration_tables.yaml"
    path.write_text(
        "# Woods exploration tables (BT2 pp. 35-38).\n\n" + _yaml_dump(data["exploration"]),
        encoding="utf-8",
    )


def write_hollow_yaml(data: dict[str, Any]) -> None:
    path = CURATED / "brambletrek_2_hollow_tables.yaml"
    path.write_text(
        "# Misty Hollow event tables (BT2 pp. 45-48).\n\n" + _yaml_dump(data["hollow"]),
        encoding="utf-8",
    )


def write_items_yaml(data: dict[str, Any]) -> None:
    path = CURATED / "brambletrek_2_items.yaml"
    path.write_text(
        "# Items table (BT2 p. 39).\nitems:\n" + _yaml_dump({"items": data["items"]}).split("items:\n", 1)[-1],
        encoding="utf-8",
    )


def write_player_tactics_yaml(data: dict[str, Any]) -> None:
    doc = {"player_tactics": data["player_tactics"]}
    path = CURATED / "brambletrek_2_player_tactics.yaml"
    path.write_text(
        "# Player combat tactics by Legacy (BT2 pp. 52-59).\n" + _yaml_dump(doc),
        encoding="utf-8",
    )


def write_hollow_entry_yaml(data: dict[str, Any]) -> None:
    path = CURATED / "brambletrek_2_hollow_entry.yaml"
    path.write_text(
        "# Hollow entry prompts (BT2 p. 44).\nentry:\n"
        + _yaml_dump({"entry": data["hollow_entry"]}).split("entry:\n", 1)[-1],
        encoding="utf-8",
    )


def write_hollow_exit_yaml(data: dict[str, Any]) -> None:
    path = CURATED / "brambletrek_2_hollow_exit.yaml"
    path.write_text(
        "# Hollow escape prompts (BT2 p. 49).\nexit:\n"
        + _yaml_dump({"exit": data["hollow_exit"]}).split("exit:\n", 1)[-1],
        encoding="utf-8",
    )


def write_opponent_tactics_yaml(data: dict[str, Any]) -> None:
    doc = {"opponents": data["opponent_tactics"]}
    path = CURATED / "brambletrek_2_opponent_tactics.yaml"
    path.write_text(
        "# Opponent tactics and combat reward items (BT2 pp. 61-83).\n" + _yaml_dump(doc),
        encoding="utf-8",
    )


def write_all_yaml(data: dict[str, Any]) -> None:
    write_legacies_yaml(data)
    write_arrival_yaml(data)
    write_exploration_yaml(data)
    write_hollow_yaml(data)
    write_items_yaml(data)
    write_player_tactics_yaml(data)
    write_hollow_entry_yaml(data)
    write_hollow_exit_yaml(data)
    write_opponent_tactics_yaml(data)


def check_legacies(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    yaml_path = CURATED / "brambletrek_2_legacies.yaml"
    if not yaml_path.exists():
        return ["missing legacies yaml"]
    current = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    cur_leg = current.get("legacies") or {}
    for leg_id, extracted in data["legacies"].items():
        cur = cur_leg.get(leg_id) or {}
        for field in ("health", "supplies", "morale"):
            if cur.get(field) != extracted.get(field):
                errors.append(
                    f"{leg_id}.{field}: yaml={cur.get(field)} pdf={extracted.get(field)}"
                )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Extract Brambletrek 2 curated data from PDF")
    parser.add_argument("--write-yaml", action="store_true", help="Write curated YAML files from PDF")
    parser.add_argument("--check", action="store_true", help="Compare YAML to PDF extract")
    parser.add_argument("--json", action="store_true", help="Write _bt2_extract.json")
    args = parser.parse_args(argv)

    if not PDF_PATH.is_file():
        print(f"PDF not found: {PDF_PATH}", file=sys.stderr)
        return 1

    doc = _open_doc()
    data = extract_all(doc)

    if args.write_yaml:
        write_all_yaml(data)
        print("Wrote curated YAML from PDF")

    if args.json or (not args.write_yaml and not args.check):
        EXTRACT_JSON.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Wrote {EXTRACT_JSON}")

    if args.check:
        errors = check_legacies(data)
        if errors:
            print("PDF vs YAML mismatches:")
            for err in errors:
                print(f"  - {err}")
            return 1
        print("check: legacies match PDF stats")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
