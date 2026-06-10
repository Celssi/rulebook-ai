"""In-game context for RAG and agent prompts."""

from __future__ import annotations

from dataclasses import dataclass

ARMY_LABELS_EN = {
    "": "",
    "space_marines": "Space Marines",
    "tyranids": "Tyranids",
}

PHASE_LABELS_EN = {
    "": "",
    "command": "Command",
    "movement": "Movement",
    "shooting": "Shooting",
    "charge": "Charge",
    "fight": "Fight",
}

ACTIVE_PLAYER_EN = {"": "", "me": "you", "opponent": "your opponent"}


@dataclass
class GameState:
    my_army: str = ""
    opponent_army: str = ""
    battle_round: int = 1
    phase: str = ""
    active_player: str = ""
    notes: str = ""

    def is_set(self) -> bool:
        return bool(
            self.my_army
            or self.opponent_army
            or self.phase
            or self.active_player
            or self.notes.strip()
        )

    def factions_for_retrieval(self) -> list[str] | None:
        """Bias RAG toward player's army sources plus core rules."""
        if not self.my_army:
            return None
        if self.my_army == "tyranids":
            return ["tyranids", "cards_nids", "core"]
        if self.my_army == "space_marines":
            return ["space_marines", "cards_sm", "core"]
        return ["core"]


def default_state() -> GameState:
    return GameState()


def format_for_prompt(state: GameState | None, language: str) -> str:
    if state is None or not state.is_set():
        return ""

    _ = language
    parts = ["Current game context (use when answering):"]
    if state.my_army or state.opponent_army:
        mine = ARMY_LABELS_EN.get(state.my_army, state.my_army or "?")
        opp = ARMY_LABELS_EN.get(state.opponent_army, state.opponent_army or "?")
        if state.my_army and state.opponent_army:
            parts.append(f"- You play: {mine} vs {opp}")
        elif state.my_army:
            parts.append(f"- Your army: {mine}")
        elif state.opponent_army:
            parts.append(f"- Opponent: {opp}")
    if state.battle_round >= 1:
        parts.append(f"- Battle round: {state.battle_round}")
    if state.phase:
        parts.append(f"- Phase: {PHASE_LABELS_EN.get(state.phase, state.phase)}")
    if state.active_player:
        parts.append(f"- Active player: {ACTIVE_PLAYER_EN.get(state.active_player, state.active_player)}")
    if state.notes.strip():
        parts.append(f"- Notes: {state.notes.strip()}")
    parts.append(
        "Prioritize rules relevant to the current phase and Core Rules when the question is about actions."
    )
    return "\n".join(parts)


def format_summary(state: GameState | None, language: str) -> str:
    """Short one-line summary for the UI banner."""
    if state is None or not state.is_set():
        return ""

    _ = language
    bits = []
    if state.battle_round >= 1:
        bits.append(f"Round {state.battle_round}")
    if state.phase:
        bits.append(PHASE_LABELS_EN.get(state.phase, state.phase))
    if state.my_army and state.opponent_army:
        bits.append(
            f"{ARMY_LABELS_EN.get(state.my_army, state.my_army)} vs "
            f"{ARMY_LABELS_EN.get(state.opponent_army, state.opponent_army)}"
        )
    elif state.my_army:
        bits.append(ARMY_LABELS_EN.get(state.my_army, state.my_army))
    return " · ".join(bits)


def game_state_from_dict(data: dict) -> GameState:
    return GameState(
        my_army=data.get("my_army", "") or "",
        opponent_army=data.get("opponent_army", "") or "",
        battle_round=int(data.get("battle_round", 1) or 1),
        phase=data.get("phase", "") or "",
        active_player=data.get("active_player", "") or "",
        notes=data.get("notes", "") or "",
    )


def game_state_to_dict(state: GameState) -> dict:
    return {
        "my_army": state.my_army,
        "opponent_army": state.opponent_army,
        "battle_round": state.battle_round,
        "phase": state.phase,
        "active_player": state.active_player,
        "notes": state.notes,
    }
