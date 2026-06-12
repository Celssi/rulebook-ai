"""Play session context without Streamlit."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from src.games.saves.keys import session_extra_key, slot_entity_key
from src.games.saves.session import PlaySession, load_session, save_session
from src.llm import ChatProvider
from src.play_tools import deck_scope_key, get_deck_snapshot, sync_deck_store

# Keep in sync with registry.DEFAULT_GAME_ID — do not import src.config here (circular import).
_DEFAULT_GAME_ID = "40k"


@dataclass
class PlayContext:
    """In-memory play state for one game slot."""

    game_id: str
    slot_id: str = ""
    entity: dict | None = None
    messages: list[dict[str, str]] = field(default_factory=list)
    deck: list[str] | None = None
    settings: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def deck_key(self) -> str:
        if self.slot_id:
            return f"deck_{self.game_id}_{self.slot_id}"
        return f"deck_{self.game_id}"

    def deck_scope(self) -> str:
        return deck_scope_key(self.game_id, self.slot_id or None)

    def sync_deck(self) -> None:
        sync_deck_store(self.deck_scope(), self.deck)

    def refresh_deck(self) -> None:
        self.deck = get_deck_snapshot(self.deck_scope())

    def get_extra(self, name: str) -> Any:
        return self.extra.get(name)

    def set_extra(self, name: str, value: Any) -> None:
        self.extra[name] = value

    def to_play_session(self) -> PlaySession:
        return PlaySession(
            deck=self.deck,
            messages=list(self.messages),
            settings=dict(self.settings),
            extra=dict(self.extra),
        )

    @classmethod
    def from_play_session(cls, game_id: str, slot_id: str, session: PlaySession) -> PlayContext:
        return cls(
            game_id=game_id,
            slot_id=slot_id,
            deck=session.deck,
            messages=list(session.messages),
            settings=dict(session.settings),
            extra=dict(session.extra),
        )


@dataclass
class AppSession:
    """Browser/API session spanning games and app settings."""

    session_id: str
    selected_game_id: str = _DEFAULT_GAME_ID
    chat_provider: ChatProvider = "ollama"
    mode: str = "RAG"
    top_k: int = 5
    retrieval_profile: str = "Fast"
    selected_factions: list[str] | None = None
    last_sources: list[dict] = field(default_factory=list)
    messages: list[dict[str, str]] = field(default_factory=list)
    game_state_40k: dict = field(default_factory=dict)
    play: dict[str, PlayContext] = field(default_factory=dict)

    def play_context(self, game_id: str | None = None) -> PlayContext:
        gid = game_id or self.selected_game_id
        if gid not in self.play:
            self.play[gid] = PlayContext(game_id=gid)
        return self.play[gid]


class SessionManager:
    """In-memory session store for local API use."""

    def __init__(self) -> None:
        self._sessions: dict[str, AppSession] = {}

    def create(self) -> AppSession:
        session_id = uuid.uuid4().hex
        app = AppSession(session_id=session_id)
        self._sessions[session_id] = app
        return app

    def get(self, session_id: str) -> AppSession | None:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: str | None) -> AppSession:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create()


def load_play_context_from_disk(store, slot_id: str) -> PlayContext:
    """Load entity + session files into PlayContext."""
    from src.games.saves.keys import slot_entity_key

    entity = store.profile.entity_to_dict(store.load_entity(slot_id))
    session = load_session(store.game_id, slot_id)
    ctx = PlayContext.from_play_session(store.game_id, slot_id, session)
    ctx.entity = entity
    ctx.refresh_deck()
    return ctx


def persist_play_context(store, ctx: PlayContext) -> None:
    """Save entity + session from PlayContext to disk."""
    if not ctx.slot_id:
        return
    if ctx.entity is not None:
        entity = store.profile.entity_from_dict(ctx.entity)
        if isinstance(entity, dict):
            entity["id"] = ctx.slot_id
        elif hasattr(entity, "id"):
            entity.id = ctx.slot_id
        store.save_entity(entity)
    ctx.sync_deck()
    save_session(store.game_id, ctx.slot_id, ctx.to_play_session())
