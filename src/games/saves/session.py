"""Per-slot play session state (deck, chat, settings, game extras)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from src.games.saves.storage import slot_data_path


@dataclass
class PlaySession:
    deck: list[str] | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    settings: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "deck": self.deck,
            "messages": self.messages,
            "settings": self.settings,
            "extra": self.extra,
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> PlaySession:
        if not data:
            return cls()
        messages = data.get("messages") or []
        if not isinstance(messages, list):
            messages = []
        settings = data.get("settings") or {}
        if not isinstance(settings, dict):
            settings = {}
        extra = data.get("extra") or {}
        if not isinstance(extra, dict):
            extra = {}
        return cls(
            deck=data.get("deck"),
            messages=[
                {"role": str(m.get("role", "user")), "content": str(m.get("content", ""))}
                for m in messages
                if isinstance(m, dict)
            ],
            settings=settings,
            extra=extra,
        )


def load_session(game_id: str, slot_id: str) -> PlaySession:
    path = slot_data_path(game_id, slot_id, "session.json")
    if not path.exists():
        return PlaySession()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return PlaySession()
    return PlaySession.from_dict(data if isinstance(data, dict) else None)


def save_session(game_id: str, slot_id: str, session: PlaySession) -> None:
    path = slot_data_path(game_id, slot_id, "session.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2), encoding="utf-8")
