"""FastAPI dependencies."""

from __future__ import annotations

from fastapi import Cookie, Header

from api.services.session_service import ensure_app_session
from src.games.saves import AppSession

SESSION_COOKIE = "rulebook_session_id"


def get_app_session(
    x_session_id: str | None = Header(default=None, alias="X-Session-Id"),
    session_id: str | None = Cookie(default=None, alias=SESSION_COOKIE),
) -> AppSession:
    sid = x_session_id or session_id
    return ensure_app_session(sid)
