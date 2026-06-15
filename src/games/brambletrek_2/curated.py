"""Load curated Brambletrek 2 YAML tables and resolve card lookups."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

import yaml

from src.games.brambletrek_2.character import (
    Brambletrek2Character,
    STAT_MAX,
    STAT_MIN,
    arrival_band,
)
from src.settings import CURATED_DIR

_RANK_ALIASES = {
    "a": "ace",
    "ace": "ace",
    "j": "jack",
    "jack": "jack",
    "q": "queen",
    "queen": "queen",
    "k": "king",
    "king": "king",
}

_CARD_RE = re.compile(
    r"^\s*(?P<rank>[2-9]|10|[ajqk]|ace|jack|queen|king)\s+of\s+"
    r"(?P<suit>hearts|diamonds|clubs|spades)\s*$",
    re.IGNORECASE,
)

_ALL_RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")


def _load_yaml(name: str) -> dict[str, Any]:
    path = CURATED_DIR / name
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


@lru_cache(maxsize=1)
def _exploration_tables() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_exploration_tables.yaml")


@lru_cache(maxsize=1)
def _recovery_tables() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_recovery_tables.yaml")


@lru_cache(maxsize=1)
def _items_table() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_items.yaml")


@lru_cache(maxsize=1)
def _combat_reference() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_combat_reference.yaml")


@lru_cache(maxsize=1)
def _player_tactics() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_player_tactics.yaml")


@lru_cache(maxsize=1)
def _opponent_tactics() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_opponent_tactics.yaml")


@lru_cache(maxsize=1)
def _opponents() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_opponents.yaml")


@lru_cache(maxsize=1)
def _legacies_data() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_legacies.yaml")


@lru_cache(maxsize=1)
def _arrival_table() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_how_did_i_get_here.yaml")


@lru_cache(maxsize=1)
def _hollow_tables() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_hollow_tables.yaml")


@lru_cache(maxsize=1)
def _hollow_entry() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_hollow_entry.yaml")


@lru_cache(maxsize=1)
def _hollow_exit() -> dict[str, Any]:
    return _load_yaml("brambletrek_2_hollow_exit.yaml")


def parse_playing_card(card: str) -> dict[str, Any] | None:
    m = _CARD_RE.match(card.strip())
    if not m:
        return None
    raw_rank = m.group("rank").lower()
    rank_key = _RANK_ALIASES.get(raw_rank, raw_rank)
    suit = m.group("suit").lower()
    if rank_key == "ace":
        numeric = 11
    elif rank_key in ("jack", "queen", "king"):
        numeric = 10
    else:
        numeric = int(rank_key)
    return {"suit": suit, "rank_key": rank_key, "numeric_value": numeric, "card": card.strip()}


def is_red_suit(suit: str) -> bool:
    return suit.lower() in ("hearts", "diamonds")


def recovery_band(rank_key: str) -> str:
    if rank_key in ("jack", "queen"):
        return "jack-queen"
    if rank_key in ("king", "ace"):
        return "king-ace"
    n = int(rank_key)
    if 2 <= n <= 4:
        return "2-4"
    if 5 <= n <= 7:
        return "5-7"
    return "8-10"


def legacy_meta(legacy_id: str) -> dict[str, Any]:
    return (_legacies_data().get("legacies") or {}).get(legacy_id) or {}


def legacy_options() -> dict[str, dict[str, str]]:
    data = _legacies_data().get("legacies") or {}
    options: dict[str, dict[str, str]] = {
        "": {"label": "— Not set —", "tagline": "", "ability": ""},
    }
    for leg_id, meta in data.items():
        if isinstance(meta, dict):
            abilities = legacy_abilities(str(leg_id))
            summary = abilities[0]["label"] if abilities else ""
            if len(abilities) > 1:
                summary = f"{len(abilities)} daily abilities"
            options[str(leg_id)] = {
                "label": meta.get("label", str(leg_id)),
                "tagline": meta.get("tagline", ""),
                "ability": summary,
            }
    return options


def legacy_abilities(legacy_id: str) -> list[dict[str, Any]]:
    meta = legacy_meta(legacy_id)
    return [dict(r) for r in (meta.get("abilities") or []) if isinstance(r, dict)]


def overcome_the_odds() -> dict[str, str]:
    row = _legacies_data().get("overcome_the_odds") or {}
    return {
        "id": "overcome_the_odds",
        "label": row.get("label", "Overcome the Odds"),
        "description": str(row.get("description", "")).strip(),
    }


def reset_daily_legacy_abilities(char: Brambletrek2Character) -> None:
    char.legacy_abilities_used = {}


def legacy_id_by_roll(total: int) -> str:
    ids = [k for k in (_legacies_data().get("legacies") or {}) if k]
    if not ids:
        return "pooh"
    return ids[(total - 1) % len(ids)]


def legacy_by_roll(total: int) -> str:
    lid = legacy_id_by_roll(total)
    return legacy_meta(lid).get("label", lid)


def lookup_exploration_event(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_exploration_tables().get(parsed["suit"]) or {}).get(parsed["rank_key"])
    if not isinstance(row, dict):
        return None
    return {**row, "suit": parsed["suit"], "rank_key": parsed["rank_key"], "card": parsed["card"]}


def lookup_hollow_event(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_hollow_tables().get(parsed["suit"]) or {}).get(parsed["rank_key"])
    if not isinstance(row, dict):
        return None
    return {**row, "suit": parsed["suit"], "rank_key": parsed["rank_key"], "card": parsed["card"]}


def lookup_hollow_entry(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_hollow_entry().get("entry") or {}).get(parsed["rank_key"])
    if not isinstance(row, dict):
        return None
    return {**row, "card": parsed["card"]}


def lookup_hollow_exit(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_hollow_exit().get("exit") or {}).get(parsed["rank_key"])
    if not isinstance(row, dict):
        return None
    return {**row, "card": parsed["card"]}


def lookup_arrival(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    band = arrival_band(parsed["rank_key"])
    row = (_arrival_table().get("bands") or {}).get(band)
    if not isinstance(row, dict):
        return None
    return {**row, "band": band, "card": parsed["card"]}


def lookup_recovery(stat: str, card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    band = recovery_band(parsed["rank_key"])
    row = (_recovery_tables().get(stat) or {}).get(band)
    if not isinstance(row, dict):
        return None
    return {**row, "stat": stat, "band": band, "card": parsed["card"]}


def lookup_item(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_items_table().get("items") or {}).get(parsed["rank_key"])
    if not isinstance(row, dict):
        return None
    return {**row, "card": parsed["card"]}


def lookup_opponent_by_rank(card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_opponents().get("by_rank") or {}).get(parsed["rank_key"])
    if not isinstance(row, dict):
        return None
    return {**row, "rank_key": parsed["rank_key"], "card": parsed["card"]}


def lookup_opponent_tactic(opponent_id: str, card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed or not opponent_id:
        return None
    foe = (_opponent_tactics().get("opponents") or {}).get(opponent_id) or {}
    row = (foe.get("tactics") or {}).get(parsed["rank_key"])
    if not row:
        return None
    return {
        "opponent_id": opponent_id,
        "rank_key": parsed["rank_key"],
        "card": parsed["card"],
        "effect": str(row),
    }


def lookup_opponent_reward(opponent_id: str, card: str) -> dict[str, Any] | None:
    parsed = parse_playing_card(card)
    if not parsed or not opponent_id:
        return None
    foe = (_opponent_tactics().get("opponents") or {}).get(opponent_id) or {}
    row = (foe.get("reward_items") or {}).get(parsed["rank_key"])
    if not row:
        return None
    return {"opponent_id": opponent_id, "card": parsed["card"], "label": str(row)}


def lookup_player_tactic(legacy_id: str, card: str) -> dict[str, Any] | None:
    if not legacy_id:
        return None
    parsed = parse_playing_card(card)
    if not parsed:
        return None
    row = (_player_tactics().get("player_tactics") or {}).get(legacy_id, {}).get(
        parsed["rank_key"]
    )
    if not row:
        return None
    return {
        "legacy": legacy_id,
        "rank_key": parsed["rank_key"],
        "card": parsed["card"],
        "effect": str(row),
    }


def event_needs_item_draw(event: dict[str, Any] | None) -> bool:
    return bool(event and "item" in (event.get("tags") or []))


def event_triggers_hollow(event: dict[str, Any] | None) -> bool:
    return bool(event and "hollow" in (event.get("tags") or []))


def _stat_line(event: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, icon in (("health", "Health"), ("morale", "Morale"), ("supplies", "Supplies")):
        val = event.get(key)
        if val is not None and val != 0:
            sign = "+" if int(val) > 0 else ""
            parts.append(f"{icon} {sign}{val}")
    if event.get("all_stats") is not None:
        v = int(event["all_stats"])
        sign = "+" if v > 0 else ""
        parts.append(f"All stats {sign}{v}")
    if event.get("combat"):
        parts.append("**Combat**")
    mf = event.get("memory_fragments")
    if mf:
        parts.append(f"Memory fragments +{mf}")
    for tag in event.get("tags") or []:
        parts.append(f"({tag.upper()})")
    return ", ".join(parts) if parts else "—"


def apply_event_deltas(char: Brambletrek2Character, event: dict[str, Any]) -> None:
    for key in ("health", "morale", "supplies"):
        delta = event.get(key)
        if delta is not None:
            setattr(char, key, getattr(char, key) + int(delta))
    all_delta = event.get("all_stats")
    if all_delta is not None:
        d = int(all_delta)
        char.health += d
        char.morale += d
        char.supplies += d
    mf = event.get("memory_fragments")
    if mf:
        char.memory_fragments += int(mf)
    char.clamp_stats()


def format_exploration_events(cards: list[str], labels: list[str] | None = None) -> str:
    labels = labels or [f"Event {i + 1}" for i in range(len(cards))]
    lines = ["**Curated exploration events** (BT2 pp. 35–38):"]
    for label, card in zip(labels, cards):
        event = lookup_exploration_event(card)
        if not event:
            lines.append(f"- **{label}** ({card}): _no curated row_")
            continue
        color = "favourable" if is_red_suit(event["suit"]) else "unfortunate"
        lines.append(
            f"- **{label}** — {card} [{color}]: **{event.get('label', '?')}** ({_stat_line(event)})"
        )
    return "\n".join(lines)


def format_recovery_draw(stat: str, card: str) -> str:
    row = lookup_recovery(stat, card)
    if not row:
        return f"**{stat.title()} recovery** — {card}: _no curated row_"
    return (
        f"**{stat.title()} recovery** — {card} (band {row.get('band', '?')}): "
        f"**{row.get('label', '?')}**"
    )


def format_item_draw(card: str) -> str:
    row = lookup_item(card)
    if not row:
        return f"**Item** — {card}: _no curated row_"
    effect = row.get("effect", "")
    return f"**Item** — {card}: **{row.get('label', '?')}** ({effect})"


def format_arrival_draw(card: str) -> str:
    row = lookup_arrival(card)
    if not row:
        return f"**How did I get here?** — {card}: _no curated row_"
    return f"**How did I get here?** — {card} ({row.get('band')}): **{row.get('label', '?')}**"


def format_hollow_event(card: str) -> str:
    row = lookup_hollow_event(card)
    if not row:
        return f"**Hollow** — {card}: _no curated row_"
    return f"**Hollow** — {card}: **{row.get('label', '?')}** ({_stat_line(row)})"


def _initiative_value(card: str) -> int | None:
    parsed = parse_playing_card(card)
    return int(parsed["numeric_value"]) if parsed else None


def format_combat_setup_curated(
    cards: list[str],
    *,
    legacy_id: str = "",
    legacy_label: str = "",
) -> str:
    if len(cards) < 7:
        return ""
    opp_card, your_init, opp_init = cards[0], cards[1], cards[2]
    tactic_cards = cards[3:7]
    lines = ["**Curated combat setup** (BT2 pp. 51–52):"]

    opp = lookup_opponent_by_rank(opp_card)
    if opp:
        lines.append(
            f"- Opponent draw {opp_card}: **{opp.get('label', '?')}** (HP {opp.get('health', '?')})"
        )

    yv, ov = _initiative_value(your_init), _initiative_value(opp_init)
    if yv is not None and ov is not None:
        first = "You" if yv > ov else "Opponent" if ov > yv else "Tie — redraw"
        lines.append(
            f"- Initiative: you {your_init} ({yv}) vs opponent {opp_init} ({ov}) — **{first}** first."
        )

    leg = legacy_label or legacy_id or "your Legacy"
    lines.append(f"- Your tactic hand ({leg}):")
    for i, card in enumerate(tactic_cards, 1):
        tactic = lookup_player_tactic(legacy_id, card)
        if tactic:
            lines.append(f"  - Tactic {i} ({card}): {tactic['effect']}")
        else:
            lines.append(f"  - Tactic {i} ({card}): set Legacy for tactic table.")

    if opp and opp.get("id"):
        lines.append(f"- Opponent tactics: draw on **{opp['label']}** page when opponent acts.")
    rules = (_combat_reference().get("rules") or {})
    for key in ("initiative", "tactics", "opponent_tactics", "retreat", "defeat"):
        if rules.get(key):
            lines.append(f"- {rules[key]}")
    return "\n".join(lines)


def combat_reference_summary() -> str:
    data = _combat_reference()
    if not data:
        return ""
    lines = ["**Combat reference** (BT2 curated):"]
    rules = data.get("rules") or {}
    for key in ("initiative", "tactics", "opponent_tactics"):
        if rules.get(key):
            lines.append(f"- {rules[key]}")
    return "\n".join(lines)


def apply_single_exploration_event(char: Brambletrek2Character, card: str) -> str:
    before = (char.health, char.morale, char.supplies)
    event = lookup_exploration_event(card)
    if not event:
        return f"{card}: no curated row found."
    notes: list[str] = []
    if event.get("combat"):
        notes.append("Combat — use **Combat setup**.")
    else:
        apply_event_deltas(char, event)
        stat = _stat_line(event)
        if stat != "—":
            notes.append(stat)
    if event_triggers_hollow(event):
        notes.append("Tag (Hollow) — you may enter the Misty Hollow.")
    if event_needs_item_draw(event):
        notes.append("Draw from **Item** table.")
    char.clamp_stats()
    after = (char.health, char.morale, char.supplies)
    if not event.get("combat"):
        notes.append(
            f"Health {before[0]}→{after[0]}, Morale {before[1]}→{after[1]}, "
            f"Supplies {before[2]}→{after[2]}"
        )
    return f"**{event.get('label', card)}** — " + "; ".join(notes)


def compare_overcome_odds(ability_card: str, outcome_card: str) -> dict[str, Any]:
    ap = parse_playing_card(ability_card)
    op = parse_playing_card(outcome_card)
    if not ap or not op:
        return {"ok": False, "message": "Could not parse cards."}
    av, ov = ap["numeric_value"], op["numeric_value"]
    result = "success" if av > ov else "failure"
    critical = None
    if ap["rank_key"] == "ace":
        critical = "critical_success"
    elif ap["rank_key"] == "2":
        critical = "critical_failure"
    return {
        "ok": True,
        "ability_card": ability_card,
        "outcome_card": outcome_card,
        "ability_value": av,
        "outcome_value": ov,
        "result": result,
        "critical": critical,
    }


def format_overcome_odds(ability_card: str, outcome_card: str) -> str:
    cmp = compare_overcome_odds(ability_card, outcome_card)
    if not cmp.get("ok"):
        return str(cmp.get("message", "Compare failed."))
    lines = [
        f"**Overcome the Odds** — Ability {ability_card} ({cmp['ability_value']}) vs "
        f"Outcome {outcome_card} ({cmp['outcome_value']}): **{cmp['result'].upper()}**"
    ]
    if cmp.get("critical") == "critical_success":
        lines.append("Critical success (Ace): regain stats you would have lost; combat flee + item.")
    elif cmp.get("critical") == "critical_failure":
        lines.append("Critical failure (2): double stat loss; combat surprise turn.")
    return "\n".join(lines)


def all_ranks_valid() -> list[str]:
    """Return missing rank keys for required tables."""
    missing: list[str] = []
    for suit in ("hearts", "diamonds", "spades", "clubs"):
        table = _exploration_tables().get(suit) or {}
        for rk in _ALL_RANKS:
            if rk not in table:
                missing.append(f"exploration.{suit}.{rk}")
    return missing
