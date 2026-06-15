"""Dice rolling, card deck, and slash-command helpers (no RAG deps)."""

from __future__ import annotations

import random
import re
from typing import Any, TypedDict

from src.settings import DEFAULT_GAME_ID

_DICE_RE = re.compile(
    r"^\s*(?:(?P<count>\d+)\s*)?[dD](?P<sides>\d+)(?:\s*(?P<mod_sign>[+-])\s*(?P<mod_val>\d+))?\s*$"
)

_RANKS_FULL = ("Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King")
_RANK_ALIASES = {
    "a": "Ace",
    "ace": "Ace",
    "j": "Jack",
    "jack": "Jack",
    "q": "Queen",
    "queen": "Queen",
    "k": "King",
    "king": "King",
    **{str(n): str(n) for n in range(2, 11)},
}
_SUIT_ALIASES = {
    "h": "hearts",
    "hearts": "hearts",
    "heart": "hearts",
    "♥": "hearts",
    "d": "diamonds",
    "diamonds": "diamonds",
    "diamond": "diamonds",
    "♦": "diamonds",
    "c": "clubs",
    "clubs": "clubs",
    "club": "clubs",
    "♣": "clubs",
    "s": "spades",
    "spades": "spades",
    "spade": "spades",
    "♠": "spades",
}
_CARD_OF_RE = re.compile(
    r"(?i)(?:drew|drawn|pulled|report|playing|played|got|have)?\s*"
    r"(?P<rank>ace|[akq2-9]|10|jack|queen|king)\s*(?:of\s+)?"
    r"(?P<suit>hearts|heart|diamonds|diamond|clubs|club|spades|spade|[hdcs♥♦♣♠])"
)
_CARD_SHORT_RE = re.compile(
    r"(?P<rank>[akq2-9]|10)\s*(?P<suit>[♥♦♣♠hdcs])",
    re.IGNORECASE,
)

_SUITS = ("hearts", "diamonds", "clubs", "spades")
_RANKS = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
_JOKERS = ("Joker (red)", "Joker (black)")

# Per-game (or per-character) in-memory decks synced from Streamlit session.
_deck_store: dict[str, list[str]] = {}


class DiceRollResult(TypedDict, total=False):
    ok: bool
    expression: str
    rolls: list[int]
    modifier: int
    total: int
    summary: str
    error: str | None


class CardToolResult(TypedDict, total=False):
    ok: bool
    cards: list[str]
    remaining: int
    summary: str
    error: str | None


def deck_scope_key(game_id: str, char_id: str | None = None) -> str:
    """Scope deck storage per game and optional character slot."""
    if char_id:
        return f"{game_id}:{char_id}"
    return game_id


def _resolve_deck_key(game_id: str, char_id: str | None = None) -> str:
    return deck_scope_key(game_id, char_id)


def normalize_card_name(text: str) -> str | None:
    """Parse user input to canonical 'rank of suit' (curated/deck compatible)."""
    raw = text.strip()
    if not raw:
        return None

    lower = raw.lower()
    if lower in ("joker (red)", "joker red", "red joker"):
        return "Joker (red)"
    if lower in ("joker (black)", "joker black", "black joker"):
        return "Joker (black)"

    from src.games.brambletrek.curated import parse_playing_card

    if parse_playing_card(raw):
        parsed = parse_playing_card(raw)
        return str(parsed["card"])

    m = _CARD_OF_RE.search(raw)
    if m:
        rank = _RANK_ALIASES.get(m.group("rank").lower(), m.group("rank").lower())
        suit_key = m.group("suit").lower()
        suit = _SUIT_ALIASES.get(suit_key)
        if suit:
            candidate = f"{rank} of {suit}"
            if parse_playing_card(candidate):
                return parse_playing_card(candidate)["card"]

    m2 = _CARD_SHORT_RE.search(raw)
    if m2:
        rank = _RANK_ALIASES.get(m2.group("rank").lower())
        suit = _SUIT_ALIASES.get(m2.group("suit").lower())
        if rank and suit:
            candidate = f"{rank} of {suit}"
            parsed = parse_playing_card(candidate)
            if parsed:
                return parsed["card"]

    return None


def _cards_equivalent(a: str, b: str) -> bool:
    from src.games.brambletrek.curated import parse_playing_card

    pa, pb = parse_playing_card(a), parse_playing_card(b)
    if pa and pb:
        return pa["suit"] == pb["suit"] and pa["rank_key"] == pb["rank_key"]
    return a.lower() == b.lower()


def is_physical_card_report(text: str) -> bool:
    """True if text looks like reporting a physical card pull."""
    return normalize_card_name(text) is not None and any(
        p in text.lower()
        for p in (
            "i drew",
            "i pulled",
            "drawn",
            "playing",
            "report",
            "physical",
            "got ",
            "have ",
            " of ",
        )
    )


def is_ai_draw_request(text: str) -> bool:
    """Explicit request for the app to draw a virtual card."""
    lower = text.lower()
    return any(
        p in lower
        for p in (
            "draw a card for me",
            "draw for me",
            "pull a card for me",
            "virtual draw",
            "ai draw",
        )
    )


def parse_dice_expression(expression: str) -> tuple[int, int, int] | str:
    """Parse NdM[+/-K]. Returns (count, sides, modifier) or error message."""
    expr = expression.strip()
    if not expr:
        return "Empty dice expression."

    m = _DICE_RE.match(expr)
    if not m:
        return (
            f"Invalid dice notation: {expression!r}. "
            "Use forms like d20, 2d6, or 2d6+1."
        )

    count = int(m.group("count") or 1)
    sides = int(m.group("sides"))
    modifier = 0
    if m.group("mod_sign") and m.group("mod_val"):
        mod = int(m.group("mod_val"))
        modifier = mod if m.group("mod_sign") == "+" else -mod

    if count < 1 or count > 100:
        return "Dice count must be between 1 and 100."
    if sides < 2 or sides > 1000:
        return "Die sides must be between 2 and 1000."
    return count, sides, modifier


def roll_dice(expression: str) -> DiceRollResult:
    """Roll dice from notation like d20, 2d6, or 2d6+1."""
    parsed = parse_dice_expression(expression)
    if isinstance(parsed, str):
        return {
            "ok": False,
            "expression": expression.strip(),
            "rolls": [],
            "modifier": 0,
            "total": 0,
            "summary": parsed,
            "error": parsed,
        }

    count, sides, modifier = parsed
    rolls = [random.randint(1, sides) for _ in range(count)]
    subtotal = sum(rolls)
    total = subtotal + modifier

    norm_expr = f"{count}d{sides}"
    if modifier > 0:
        norm_expr += f"+{modifier}"
    elif modifier < 0:
        norm_expr += str(modifier)

    if count == 1:
        roll_part = str(rolls[0])
    else:
        roll_part = f"[{', '.join(str(r) for r in rolls)}] = {subtotal}"

    if modifier:
        mod_str = f"+{modifier}" if modifier > 0 else str(modifier)
        summary = f"Rolled {norm_expr}: {roll_part} {mod_str} → **{total}**"
    else:
        summary = f"Rolled {norm_expr}: {roll_part} → **{total}**"

    return {
        "ok": True,
        "expression": norm_expr,
        "rolls": rolls,
        "modifier": modifier,
        "total": total,
        "summary": summary,
        "error": None,
    }


def format_dice_result(result: DiceRollResult) -> str:
    """Human-readable dice output for chat."""
    return result.get("summary") or result.get("error") or "Dice roll failed."


def build_standard_deck(with_jokers: bool = False) -> list[str]:
    cards = [f"{rank} of {suit}" for suit in _SUITS for rank in _RANKS]
    if with_jokers:
        cards.extend(_JOKERS)
    random.shuffle(cards)
    return cards


def sync_deck_store(scope_key: str, deck: list[str] | None) -> None:
    """Load deck from app session into the in-memory store."""
    if deck is not None:
        _deck_store[scope_key] = list(deck)


def get_deck_snapshot(scope_key: str) -> list[str]:
    """Return a copy of the current deck for session persistence."""
    _ensure_deck(scope_key)
    return list(_deck_store[scope_key])


def deck_remaining(scope_key: str) -> int:
    _ensure_deck(scope_key)
    return len(_deck_store[scope_key])


def _ensure_deck(scope_key: str, with_jokers: bool = False) -> None:
    if scope_key not in _deck_store:
        _deck_store[scope_key] = build_standard_deck(with_jokers=with_jokers)


def reset_deck(
    game_id: str = DEFAULT_GAME_ID,
    with_jokers: bool = False,
    char_id: str | None = None,
) -> CardToolResult:
    """Shuffle a fresh standard deck for the given scope."""
    scope = _resolve_deck_key(game_id, char_id)
    _deck_store[scope] = build_standard_deck(with_jokers=with_jokers)
    remaining = len(_deck_store[scope])
    return {
        "ok": True,
        "cards": [],
        "remaining": remaining,
        "summary": f"Deck reset and shuffled ({remaining} cards).",
        "error": None,
    }


def register_physical_card(
    card_text: str,
    *,
    game_id: str = DEFAULT_GAME_ID,
    char_id: str | None = None,
) -> CardToolResult:
    """Record a physical card pull and remove it from the virtual deck."""
    canonical = normalize_card_name(card_text)
    if not canonical:
        return {
            "ok": False,
            "cards": [],
            "remaining": deck_remaining(_resolve_deck_key(game_id, char_id)),
            "summary": f"Could not parse card: {card_text!r}. Try 'Queen of Hearts' or 'Q♥'.",
            "error": "Invalid card",
        }

    scope = _resolve_deck_key(game_id, char_id)
    _ensure_deck(scope)
    deck = _deck_store[scope]
    match_idx = None
    for i, c in enumerate(deck):
        if _cards_equivalent(c, canonical):
            match_idx = i
            break

    if match_idx is None:
        return {
            "ok": False,
            "cards": [canonical],
            "remaining": len(deck),
            "summary": (
                f"**{canonical}** is not in the deck "
                f"({len(deck)} cards remaining — already drawn or not in deck?)."
            ),
            "error": "Card not in deck",
        }

    deck.pop(match_idx)
    remaining = len(deck)
    return {
        "ok": True,
        "cards": [canonical],
        "remaining": remaining,
        "summary": f"Recorded physical card **{canonical}** ({remaining} cards left).",
        "error": None,
    }


def draw_cards(
    count: int = 1,
    with_jokers: bool = False,
    game_id: str = DEFAULT_GAME_ID,
    char_id: str | None = None,
) -> CardToolResult:
    """Draw cards from the scoped deck."""
    scope = _resolve_deck_key(game_id, char_id)
    if count < 1:
        return {
            "ok": False,
            "cards": [],
            "remaining": deck_remaining(scope),
            "summary": "Draw count must be at least 1.",
            "error": "Draw count must be at least 1.",
        }
    if count > 52:
        return {
            "ok": False,
            "cards": [],
            "remaining": deck_remaining(scope),
            "summary": "Cannot draw more than 52 cards at once.",
            "error": "Cannot draw more than 52 cards at once.",
        }

    _ensure_deck(scope, with_jokers=with_jokers)
    deck = _deck_store[scope]
    if len(deck) < count:
        return {
            "ok": False,
            "cards": deck.copy(),
            "remaining": len(deck),
            "summary": (
                f"Not enough cards left (requested {count}, {len(deck)} remaining). "
                "Use /deck reset or the sidebar to reshuffle."
            ),
            "error": "Deck depleted",
        }

    drawn = [deck.pop() for _ in range(count)]
    remaining = len(deck)
    if count == 1:
        summary = f"Drew **{drawn[0]}** ({remaining} cards left)."
    else:
        listed = ", ".join(drawn)
        summary = f"Drew {count} cards: {listed} ({remaining} cards left)."
    return {
        "ok": True,
        "cards": drawn,
        "remaining": remaining,
        "summary": summary,
        "error": None,
    }


def format_card_result(result: CardToolResult) -> str:
    return result.get("summary") or result.get("error") or "Card draw failed."


def clear_deck_store() -> None:
    """Clear all in-memory decks (mainly for tests)."""
    _deck_store.clear()


# --- Intent and command parsing ---

_DICE_NOTATION_RE = re.compile(r"(?<!\w)(?:\d+)?[dD]\d+(?:\s*[+-]\s*\d+)?(?!\w)")


def extract_dice_expression(text: str) -> str | None:
    """Pull first dice notation from natural language."""
    m = _DICE_NOTATION_RE.search(text)
    if m:
        return m.group(0).replace(" ", "")
    lower = text.lower()
    for sides in (20, 12, 10, 8, 6, 4, 100):
        if f"d{sides}" in lower or f"d {sides}" in lower:
            return f"d{sides}"
    return None


def is_dice_question(text: str) -> bool:
    lower = text.lower()
    if lower.startswith("/roll"):
        return True
    interpretive = (
        "what does",
        "what do",
        "mean",
        "explain",
        "interpret",
        "according to",
        "rule say",
        "rules say",
    )
    if any(p in lower for p in interpretive):
        return False
    if _DICE_NOTATION_RE.search(text) and any(
        w in lower for w in ("roll", "rolled", "rolling", "reroll")
    ):
        return True
    dice_words = ("roll", "rolled", "rolling", "reroll")
    if any(w in lower for w in dice_words):
        if extract_dice_expression(text) or any(
            f"d{n}" in lower for n in (4, 6, 8, 10, 12, 20, 100)
        ):
            return True
    return False


def is_card_question(text: str) -> bool:
    lower = text.lower()
    if lower.startswith("/draw") or lower.startswith("/deck"):
        return True
    card_words = (
        "draw",
        "drew",
        "card",
        "cards",
        "deck",
        "shuffle",
        "ace",
        "king",
        "queen",
        "jack",
        "joker",
    )
    if not any(w in lower for w in card_words):
        return False
    if is_dice_question(text) and not any(
        w in lower for w in ("card", "cards", "deck", "draw", "shuffle", "ace", "king", "queen", "jack")
    ):
        return False
    return True


def is_card_plus_rules_question(text: str) -> bool:
    """Draw (or cite a card) and explain meaning from rule tables."""
    lower = text.lower()
    rulesish = any(
        k in lower
        for k in (
            "reason",
            "background",
            "adventure",
            "keyword",
            "what does",
            "explain",
            "mean",
            "table",
        )
    )
    if not rulesish:
        return False
    if is_card_question(text) or "draw" in lower:
        return True
    if any(
        k in lower
        for k in ("reason for adventure", "background table", "i got", "i drew", "pulled")
    ) and any(
        s in lower
        for s in ("spade", "heart", "club", "diamond", "ace", "jack", "queen", "king", "joker")
    ):
        return True
    return False


def parse_explicit_command(text: str) -> dict[str, Any] | None:
    """Parse /roll, /draw, /deck reset. Returns None if not a command."""
    stripped = text.strip()
    lower = stripped.lower()

    if lower.startswith("/roll"):
        expr = stripped[5:].strip() or "d6"
        return {"kind": "roll", "expression": expr}

    if lower.startswith("/draw"):
        rest = stripped[5:].strip()
        count = 1
        if rest:
            try:
                count = int(rest.split()[0])
            except ValueError:
                return {
                    "kind": "error",
                    "message": f"Invalid draw count: {rest!r}. Use /draw or /draw 3.",
                }
        return {"kind": "draw", "count": count}

    if lower in {"/deck reset", "/deck reshuffle", "/deck"}:
        return {"kind": "reset_deck"}

    if lower.startswith("/deck"):
        rest = stripped[5:].strip().lower()
        if rest in {"reset", "reshuffle", ""}:
            return {"kind": "reset_deck"}
        return {
            "kind": "error",
            "message": f"Unknown deck command: {rest!r}. Use /deck reset.",
        }

    if lower.startswith("/log"):
        rest = stripped[4:].strip()
        if not rest:
            return {"kind": "error", "message": "Use /log your Lonelog line here."}
        return {"kind": "log", "text": rest}

    return None


def run_explicit_command(
    text: str,
    game_id: str = DEFAULT_GAME_ID,
    char_id: str | None = None,
) -> dict[str, Any] | None:
    """Execute explicit slash command; returns result dict or None."""
    cmd = parse_explicit_command(text)
    if cmd is None:
        return None

    if cmd.get("kind") == "error":
        return {"ok": False, "route": "command", "answer": cmd["message"], "sources": []}

    if cmd["kind"] == "log":
        return {
            "ok": True,
            "route": "log",
            "answer": f"Logged: {cmd['text']}",
            "sources": [],
            "log_text": cmd["text"],
        }

    if cmd["kind"] == "roll":
        result = roll_dice(cmd["expression"])
        return {
            "ok": result["ok"],
            "route": "dice",
            "answer": format_dice_result(result),
            "sources": [],
            "tool_result": result,
        }

    if cmd["kind"] == "draw":
        result = draw_cards(count=cmd["count"], game_id=game_id, char_id=char_id)
        return {
            "ok": result["ok"],
            "route": "cards",
            "answer": format_card_result(result),
            "sources": [],
            "tool_result": result,
        }

    if cmd["kind"] == "reset_deck":
        result = reset_deck(game_id=game_id, char_id=char_id)
        return {
            "ok": True,
            "route": "cards",
            "answer": format_card_result(result),
            "sources": [],
            "tool_result": result,
        }

    return None
