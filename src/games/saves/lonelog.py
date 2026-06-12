"""Generic [Lonelog](https://lonelog.readthedocs.io/) v1.5 append-only session logs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, Iterable, Sequence

from src.games.saves.storage import slot_data_path

# ---------------------------------------------------------------------------
# Playing-card shorthand (deck draws)
# ---------------------------------------------------------------------------

_RANK_SHORT = {
    "Ace": "A",
    "Jack": "J",
    "Queen": "Q",
    "King": "K",
}
_SUIT_SHORT = {
    "hearts": "♥",
    "diamonds": "♦",
    "clubs": "♣",
    "spades": "♠",
}


def card_short_label(card: str) -> str:
    """Queen of Hearts -> Q♥"""
    parts = card.split(" of ", 1)
    if len(parts) != 2:
        return card
    rank_raw, suit = parts[0].strip(), parts[1].strip().lower()
    rank_title = rank_raw.title() if rank_raw.islower() else rank_raw
    r = _RANK_SHORT.get(rank_title, rank_title[:1] if rank_title.isdigit() else rank_title[:1].upper())
    s = _SUIT_SHORT.get(suit, suit[:1])
    return f"{r}{s}"


# ---------------------------------------------------------------------------
# Prefix helpers
# ---------------------------------------------------------------------------


def _ensure_prefix(line: str, prefix: str) -> str:
    stripped = line.strip()
    if stripped.startswith(prefix):
        return stripped
    return f"{prefix} {stripped}"


def _join_fields(*parts: str | None) -> str:
    return "|".join(p for p in parts if p is not None and p != "")


# ---------------------------------------------------------------------------
# Core notation (@ ? d: -> =>)
# ---------------------------------------------------------------------------


def format_player_action(text: str, *, actor: str = "") -> str:
    """@ Action or @(Name) Action."""
    stripped = text.strip()
    if stripped.startswith("@(") or stripped.startswith("@"):
        return stripped
    if actor.strip():
        return f"@({actor.strip()}) {stripped}"
    return f"@ {stripped}"


def format_oracle_question(text: str) -> str:
    return _ensure_prefix(text, "?")


def format_resolution(text: str) -> str:
    """Standalone oracle / shorthand result (-> Yes, but...)."""
    return _ensure_prefix(text, "->")


def format_mechanical(text: str) -> str:
    """Mechanical update not covered by d: (-> Morale -1)."""
    stripped = text.strip()
    if stripped.startswith("->"):
        return stripped
    return f"-> {stripped}"


def format_narrative(text: str) -> str:
    return _ensure_prefix(text, "=>")


def format_meta_note(text: str, *, kind: str = "note") -> str:
    """(note: ...) — reflection, reminder, house rule."""
    stripped = text.strip()
    if stripped.startswith("("):
        return stripped
    label = kind.strip() or "note"
    return f"({label}: {stripped})"


def format_dialogue(speaker: str, line: str) -> str:
    """N (Guard): \"Who's there?\" or PC: \"Stay calm.\" """
    text = line.strip().strip('"')
    name = speaker.strip()
    if name.upper() == "PC":
        return f'PC: "{text}"'
    return f'N ({name}): "{text}"'


def format_narrative_block(text: str) -> list[str]:
    """In-fiction document block (\\--- ... ---\\)."""
    body = text.strip("\n")
    return ["\\---", body, "---\\"]


def format_draw(cards: list[str], *, label: str = "Drew") -> str:
    if not cards:
        return f"d: {label} (none)"
    if len(cards) == 1:
        return f"d: {label} {cards[0]}"
    listed = ", ".join(cards)
    return f"d: {label} {len(cards)} -> {listed}"


def format_roll(expression: str, summary: str) -> str:
    """Legacy helper — prefer format_dice_roll for new code."""
    expr = expression.strip()
    body = summary.strip()
    if body:
        if "->" in body or body.startswith("="):
            return f"d: {expr} {body}" if not body.startswith("->") else f"d: {expr} {body}"
        return f"d: {expr} -> {body}"
    return f"d: {expr}"


def format_dice_roll(
    expression: str,
    *,
    rolls: Sequence[int] | None = None,
    total: int | None = None,
    modifier: int = 0,
    vs: int | None = None,
    vs_label: str = "TN",
    outcome: str | None = None,
    roll_context: Sequence[str] | None = None,
    comparison: str | None = None,
) -> str:
    """
    Lonelog mechanics line: d: 2d6=8 vs TN 7 -> Success

    comparison: optional shorthand like \"5≥4 S\" or \"2≤4 F\"
    """
    expr = expression.strip()
    roll_part = ""
    if rolls is not None and rolls:
        if len(rolls) == 1:
            shown = rolls[0]
            if total is not None and modifier:
                shown = total - modifier
            roll_part = f"={shown}"
            if modifier:
                mod = f"+{modifier}" if modifier > 0 else str(modifier)
                roll_part += mod
            if total is not None and (len(rolls) > 1 or modifier):
                roll_part += f"={total}"
        else:
            roll_part = f"=[{', '.join(str(r) for r in rolls)}]"
            if total is not None:
                if modifier:
                    mod = f"+{modifier}" if modifier > 0 else str(modifier)
                    roll_part += f" {mod}={total}"
                else:
                    roll_part += f" = {total}"
    elif total is not None:
        roll_part = f"={total}"

    ctx = ""
    if roll_context:
        inner = " | ".join(roll_context)
        ctx = f" [{inner}]"

    if comparison:
        core = f"d: {comparison}{ctx}"
    else:
        core = f"d: {expr}{roll_part}{ctx}"

    if vs is not None:
        core += f" vs {vs_label} {vs}"
    if outcome:
        core += f" -> {outcome.strip()}"
    return core


def format_dice_from_result(
    result: dict[str, Any],
    *,
    vs: int | None = None,
    vs_label: str = "TN",
    outcome: str | None = None,
) -> str:
    """Build a Lonelog d: line from roll_dice() output."""
    if not result.get("ok"):
        return format_mechanical(result.get("error") or result.get("summary") or "Roll failed")
    rolls = result.get("rolls") or []
    total = result.get("total")
    return format_dice_roll(
        str(result.get("expression") or "d6"),
        rolls=rolls,
        total=total,
        modifier=int(result.get("modifier") or 0),
        vs=vs,
        vs_label=vs_label,
        outcome=outcome,
    )


def format_table(
    table: str,
    result: str,
    *,
    roll: str = "",
    options: Sequence[str] | None = None,
) -> str:
    """tbl: Mythic Event d100=78 -> NPC Action or tbl: Mood [A, B, C]"""
    name = table.strip()
    if options:
        opts = ", ".join(options)
        if result.strip():
            roll_bit = f" {roll.strip()}" if roll.strip() else ""
            return f"tbl: {name} [{opts}]{roll_bit} -> {result.strip()}"
        return f"tbl: {name} [{opts}]"
    roll_bit = f" {roll.strip()}" if roll.strip() else ""
    return f"tbl: {name}{roll_bit} -> {result.strip()}"


def format_generator(
    name: str,
    result: str,
    *,
    axes: dict[str, str] | None = None,
) -> str:
    """gen: NPC -> Merchant / Secretive or multi-line axis block."""
    if not axes:
        return f"gen: {name.strip()} -> {result.strip()}"
    lines = [f"gen: {name.strip()}"]
    for axis, val in axes.items():
        lines.append(f"  {axis}: {val.strip()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Persistent tags (core §4.1)
# ---------------------------------------------------------------------------


def format_tag(kind: str, name: str, *fields: str, reference: bool = False) -> str:
    """Generic [Kind:Name|field|field] tag."""
    prefix = f"#{kind}" if reference else kind
    body = _join_fields(name, *fields)
    return f"[{prefix}:{body}]"


def format_npc(name: str, *tags: str, reference: bool = False) -> str:
    return format_tag("N", name, *tags, reference=reference)


def format_location(name: str, *tags: str, reference: bool = False) -> str:
    return format_tag("L", name, *tags, reference=reference)


def format_event(name: str, current: int, total: int) -> str:
    return f"[E:{name} {current}/{total}]"


def format_thread(name: str, state: str = "Open") -> str:
    return f"[Thread:{name}|{state}]"


def format_pc(name: str, *stats: str) -> str:
    body = _join_fields(name, *stats)
    return f"[PC:{body}]"


def format_clock(name: str, current: int, total: int) -> str:
    return f"[Clock:{name} {current}/{total}]"


def format_track(name: str, current: int, total: int) -> str:
    return f"[Track:{name} {current}/{total}]"


def format_timer(name: str, remaining: int) -> str:
    return f"[Timer:{name} {remaining}]"


# ---------------------------------------------------------------------------
# Add-on tags (combat, resources, dungeon)
# ---------------------------------------------------------------------------


def format_foe(name: str, *stats: str) -> str:
    body = _join_fields(name, *stats)
    return f"[F:{body}]"


def format_inv(item: str, *props: str) -> str:
    body = _join_fields(item, *props)
    return f"[Inv:{body}]"


def format_wealth(*currencies: str) -> str:
    """[Wealth:Gold 45|Silver 12] or [Wealth:Gold+15]"""
    body = "|".join(currencies)
    return f"[Wealth:{body}]"


def format_room(
    room_id: str,
    status: str = "",
    description: str = "",
    *,
    exits: str = "",
    reference: bool = False,
) -> str:
    prefix = "#R" if reference else "R"
    parts = [room_id]
    if status:
        parts.append(status)
    if description:
        parts.append(description)
    if exits:
        parts.append(f"exits {exits}")
    body = "|".join(parts)
    return f"[{prefix}:{body}]"


def format_block(name: str, *, close: bool = False) -> str:
    """[COMBAT], [/COMBAT], [RESOURCES], [DUNGEON STATUS], etc."""
    tag = f"/{name}" if close else name
    return f"[{tag}]"


# ---------------------------------------------------------------------------
# Structure (sessions, scenes)
# ---------------------------------------------------------------------------


def format_scene(
    scene_id: str | int,
    context: str = "",
    *,
    suffix: str = "",
    markdown: bool = False,
    combat: bool = False,
    room_tag: str = "",
) -> str:
    """
    S1 *Dark alley, midnight* or ### S1 *...* (markdown heading).

    suffix: flashback letter (a, b) or montage decimal (.1)
    """
    sid = f"S{scene_id}{suffix}"
    extras = " ".join(x for x in (room_tag.strip(), "[COMBAT]" if combat else "") if x)
    ctx = context.strip()
    if ctx:
        core = f"{sid} *{ctx}*"
    else:
        core = sid
    line = f"{core} {extras}".strip() if extras else core
    return f"### {line}" if markdown else line


def format_session_header(
    session_num: int,
    *,
    date_str: str = "",
    duration: str = "",
    scenes: str = "",
    recap: str = "",
    goals: str = "",
    markdown: bool = True,
) -> list[str]:
    """## Session 1 with optional metadata lines."""
    title = f"Session {session_num}"
    heading = f"## {title}" if markdown else f"=== {title} ==="
    lines = [heading]
    meta_parts = []
    if date_str:
        meta_parts.append(f"Date: {date_str}")
    if duration:
        meta_parts.append(f"Duration: {duration}")
    if scenes:
        meta_parts.append(f"Scenes: {scenes}")
    if meta_parts:
        lines.append(f"*{' | '.join(meta_parts)}*")
    if recap:
        lines.append(f"**Recap:** {recap}")
    if goals:
        lines.append(f"**Goals:** {goals}")
    return lines


@dataclass
class CampaignHeader:
    """YAML front matter for digital Lonelog files."""

    title: str
    ruleset: str = ""
    game_id: str = ""
    slot_id: str = ""
    player: str = ""
    pcs: str = ""
    start_date: str = ""
    last_update: str = ""
    tools: str = ""
    themes: str = ""
    tone: str = ""
    notes: str = ""
    extra: dict[str, str] = field(default_factory=dict)

    def to_yaml(self) -> str:
        rows: list[tuple[str, str]] = [
            ("title", self.title),
            ("ruleset", self.ruleset),
            ("game", self.game_id),
            ("slot_id", self.slot_id),
            ("player", self.player),
            ("pcs", self.pcs),
            ("start_date", self.start_date or date.today().isoformat()),
            ("last_update", self.last_update or date.today().isoformat()),
            ("tools", self.tools),
            ("themes", self.themes),
            ("tone", self.tone),
            ("notes", self.notes),
        ]
        rows.extend(self.extra.items())
        body = "\n".join(f"{k}: {v}" for k, v in rows if v)
        return f"---\n{body}\n---\n"


def format_resource_block(lines: Iterable[str], *, kind: str = "RESOURCES") -> list[str]:
    """[RESOURCES] ... [/RESOURCES] snapshot block."""
    body = [ln.strip() for ln in lines if ln.strip()]
    if not body:
        return []
    return [format_block(kind), *body, format_block(kind, close=True)]


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------


class LonelogStore:
    def __init__(
        self,
        game_id: str,
        *,
        game_label: str,
        wrap_code_blocks: bool = False,
    ) -> None:
        self.game_id = game_id
        self.game_label = game_label
        self.wrap_code_blocks = wrap_code_blocks

    def path(self, slot_id: str) -> Path:
        return slot_data_path(self.game_id, slot_id, "lonelog.md")

    def _ensure_header(self, slot_id: str, display_name: str, *, campaign: CampaignHeader | None = None) -> None:
        path = self.path(slot_id)
        if path.exists():
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        name = display_name.strip() or "Session"
        parts: list[str] = []
        if campaign:
            parts.append(campaign.to_yaml())
        parts.append(f"# {self.game_label} — {name}\n")
        parts.append("_Lonelog session log_\n")
        path.write_text("\n".join(parts) + "\n", encoding="utf-8")

    def _write_lines(self, slot_id: str, lines: list[str], *, display_name: str = "") -> None:
        if not slot_id or not lines:
            return
        self._ensure_header(slot_id, display_name)
        with self.path(slot_id).open("a", encoding="utf-8") as f:
            for line in lines:
                if line == "":
                    f.write("\n")
                    continue
                f.write(line.rstrip() + "\n")

    def append(self, slot_id: str, line: str, *, display_name: str = "") -> None:
        if not slot_id or not line.strip():
            return
        if self.wrap_code_blocks and not line.startswith("```"):
            self._write_lines(slot_id, ["```", line, "```"], display_name=display_name)
        else:
            self._write_lines(slot_id, [line], display_name=display_name)

    def append_many(self, slot_id: str, lines: list[str], *, display_name: str = "") -> None:
        cleaned = [ln for ln in lines if ln is not None]
        if not slot_id or not cleaned:
            return
        self._ensure_header(slot_id, display_name)
        with self.path(slot_id).open("a", encoding="utf-8") as f:
            for line in cleaned:
                if line == "":
                    f.write("\n")
                else:
                    f.write(line.rstrip() + "\n")

    def append_session(
        self,
        slot_id: str,
        session_num: int,
        *,
        display_name: str = "",
        **kwargs: Any,
    ) -> None:
        self.append_many(slot_id, format_session_header(session_num, **kwargs), display_name=display_name)

    def append_scene(
        self,
        slot_id: str,
        scene_id: str | int,
        context: str = "",
        *,
        display_name: str = "",
        **kwargs: Any,
    ) -> None:
        self.append(slot_id, format_scene(scene_id, context, **kwargs), display_name=display_name)

    def append_block(
        self,
        slot_id: str,
        block_name: str,
        lines: list[str],
        *,
        display_name: str = "",
    ) -> None:
        payload = [format_block(block_name), *lines, format_block(block_name, close=True)]
        self.append_many(slot_id, payload, display_name=display_name)

    def recent_context(self, slot_id: str, n_lines: int = 40) -> str:
        path = self.path(slot_id)
        if not path.exists():
            return ""
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return ""
        tail = [
            ln
            for ln in lines
            if ln.strip()
            and not ln.startswith("#")
            and not ln.startswith("---")
            and ln.strip() != "_Lonelog session log_"
            and ln.strip() != "```"
        ][-n_lines:]
        if not tail:
            return ""
        return "Recent Lonelog (most recent last):\n" + "\n".join(tail)

    def read_tail(self, slot_id: str, n_lines: int = 30) -> list[str]:
        path = self.path(slot_id)
        if not path.exists():
            return []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        return lines[-n_lines:]
