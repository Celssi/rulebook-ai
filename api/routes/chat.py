"""Chat routes."""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Response
from sse_starlette.sse import EventSourceResponse

from api.deps import SESSION_COOKIE, get_app_session
from api.models import ChatRequest, ChatResponse
from api.services.chat_service import answer_user_prompt, send_chat
from api.services.session_service import app_session_payload, get_messages, sync_messages_to_context
from src.games.saves import AppSession, get_play_store
from api.services.session_service import get_active_play_context

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def post_chat(
    body: ChatRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    result = send_chat(app, body.prompt.strip())
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")
    return ChatResponse(session_id=app.session_id, **result)


@router.post("/stream")
async def stream_chat(
    body: ChatRequest,
    response: Response,
    app: AppSession = Depends(get_app_session),
):
    response.set_cookie(key=SESSION_COOKIE, value=app.session_id, httponly=True, samesite="lax")

    async def event_generator():
        messages = list(get_messages(app))
        messages.append({"role": "user", "content": body.prompt.strip()})
        yield {"event": "user", "data": json.dumps({"content": body.prompt.strip()})}
        try:
            answer, sources, route = answer_user_prompt(app, body.prompt.strip())
        except Exception as e:
            answer = f"Error: {e}"
            sources = []
            route = "error"
        messages.append({"role": "assistant", "content": answer})
        app.last_sources = sources
        sync_messages_to_context(app, messages)
        ctx = get_active_play_context(app)
        if ctx:
            store = get_play_store(app.selected_game_id)
            if store:
                store.persist_ctx(ctx)
        payload = {
            "answer": answer,
            "sources": sources,
            "route": route,
            "messages": messages,
            "session_id": app.session_id,
        }
        yield {"event": "done", "data": json.dumps(payload)}

    return EventSourceResponse(event_generator())
