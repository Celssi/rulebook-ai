"""Misty Hollow grid state machine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

HOLLOW_ROWS = 5
HOLLOW_COLS = 4


@dataclass
class HollowCell:
    card: str = ""
    revealed: bool = False

    def to_dict(self) -> dict:
        return {"card": self.card, "revealed": self.revealed}

    @staticmethod
    def from_dict(data: dict | None) -> HollowCell:
        if not data:
            return HollowCell()
        return HollowCell(
            card=str(data.get("card", "") or ""),
            revealed=bool(data.get("revealed", False)),
        )


@dataclass
class HollowState:
    entry_card: str = ""
    entry_prompt: str = ""
    grid: list[list[HollowCell]] = field(default_factory=list)
    marker_row: int = 0
    marker_col: int = 0
    moves_since_escape_attempt: int = 0

    def to_dict(self) -> dict:
        return {
            "entry_card": self.entry_card,
            "entry_prompt": self.entry_prompt,
            "grid": [[c.to_dict() for c in row] for row in self.grid],
            "marker_row": self.marker_row,
            "marker_col": self.marker_col,
            "moves_since_escape_attempt": self.moves_since_escape_attempt,
        }

    @staticmethod
    def from_dict(data: dict | None) -> HollowState | None:
        if not data:
            return None
        grid_raw = data.get("grid") or []
        grid: list[list[HollowCell]] = []
        for row in grid_raw:
            grid.append([HollowCell.from_dict(c) for c in row])
        return HollowState(
            entry_card=str(data.get("entry_card", "") or ""),
            entry_prompt=str(data.get("entry_prompt", "") or ""),
            grid=grid,
            marker_row=int(data.get("marker_row", 0) or 0),
            marker_col=int(data.get("marker_col", 0) or 0),
            moves_since_escape_attempt=int(data.get("moves_since_escape_attempt", 0) or 0),
        )


def hollow_state_to_dict(state: HollowState | None) -> dict | None:
    if state is None:
        return None
    return state.to_dict()


def hollow_state_from_dict(data: dict | None) -> HollowState | None:
    return HollowState.from_dict(data)


def _adjacent(r: int, c: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < HOLLOW_ROWS and 0 <= nc < HOLLOW_COLS:
                out.append((nr, nc))
    return out


def new_hollow_grid(cards: list[str], *, entry_card: str, entry_prompt: str) -> HollowState:
    """Build 5x4 grid from 20 cards; marker starts before row 0 col 0 (entry point)."""
    needed = HOLLOW_ROWS * HOLLOW_COLS
    deck = list(cards[:needed])
    while len(deck) < needed:
        deck.append("")
    grid: list[list[HollowCell]] = []
    idx = 0
    for _ in range(HOLLOW_ROWS):
        row: list[HollowCell] = []
        for _ in range(HOLLOW_COLS):
            row.append(HollowCell(card=deck[idx], revealed=False))
            idx += 1
        grid.append(row)
    return HollowState(
        entry_card=entry_card,
        entry_prompt=entry_prompt,
        grid=grid,
        marker_row=0,
        marker_col=0,
    )


def reveal_cell(state: HollowState, row: int, col: int) -> HollowCell | None:
    if not state.grid or row < 0 or col < 0:
        return None
    if row >= len(state.grid) or col >= len(state.grid[row]):
        return None
    cell = state.grid[row][col]
    cell.revealed = True
    state.marker_row = row
    state.marker_col = col
    state.moves_since_escape_attempt += 1
    return cell


def adjacent_unrevealed(state: HollowState) -> list[tuple[int, int]]:
    return [
        (r, c)
        for r, c in _adjacent(state.marker_row, state.marker_col)
        if not state.grid[r][c].revealed
    ]


def all_revealed(state: HollowState) -> bool:
    return all(cell.revealed for row in state.grid for cell in row)


def reshuffle_face_down(state: HollowState, new_cards: list[str]) -> None:
    """Replace face-down cards after 5 clubs (p. 43)."""
    idx = 0
    for row in state.grid:
        for cell in row:
            if not cell.revealed and idx < len(new_cards):
                cell.card = new_cards[idx]
                idx += 1


def replace_revealed_cell(state: HollowState, row: int, col: int, new_card: str) -> None:
    if state.grid and 0 <= row < len(state.grid) and 0 <= col < len(state.grid[row]):
        state.grid[row][col].card = new_card
        state.grid[row][col].revealed = False


def hollow_grid_summary(state: HollowState | None) -> str:
    if not state or not state.grid:
        return ""
    lines = [f"Entry: {state.entry_card or '—'} — {state.entry_prompt or ''}"]
    for r, row in enumerate(state.grid):
        cells = []
        for c, cell in enumerate(row):
            mark = "*" if (r, c) == (state.marker_row, state.marker_col) else ""
            if cell.revealed:
                cells.append(f"{mark}{cell.card or '?'}")
            else:
                cells.append(f"{mark}##")
        lines.append(" | ".join(cells))
    return "\n".join(lines)
