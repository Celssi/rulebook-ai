"""Shared Pydantic models for chat endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[dict[str, Any]] = Field(default_factory=list)
    route: str = ""
    messages: list[dict[str, str]] = Field(default_factory=list)
    session_id: str = ""
