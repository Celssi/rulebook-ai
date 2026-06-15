"""Shared Pydantic models for play-mode endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class SessionUpdate(BaseModel):
    selected_game_id: str | None = None
    chat_provider: str | None = None
    mode: str | None = None
    top_k: int | None = None
    retrieval_profile: str | None = None
    selected_factions: list[str] | None = None
    settings: dict[str, str] | None = None


class CharacterUpdate(BaseModel):
    entity: dict[str, Any]


class CharacterTableDrawRequest(BaseModel):
    table: str


class RosterCreate(BaseModel):
    name: str = ""


class JourneyApplyRequest(BaseModel):
    event_index: int


class ExplorationApplyRequest(BaseModel):
    event_index: int


class HollowMoveRequest(BaseModel):
    row: int
    col: int


class DeckDrawRequest(BaseModel):
    count: int = 1


class DeckReportRequest(BaseModel):
    card: str


class RollRequest(BaseModel):
    expression: str = "d6"


class GameStateUpdate(BaseModel):
    game_state: dict[str, Any]
