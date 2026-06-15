"""Chat message helpers for play context (domain layer, no API imports)."""

from __future__ import annotations

from src.games.saves.context import AppSession, PlayContext


def messages_for_context(app: AppSession, ctx: PlayContext | None) -> list[dict[str, str]]:
    if ctx is not None:
        return list(ctx.messages)
    return list(app.messages)


def sync_messages(app: AppSession, ctx: PlayContext | None, messages: list[dict[str, str]]) -> None:
    if ctx is not None:
        ctx.messages = list(messages)
    else:
        app.messages = list(messages)


def append_chat_exchange(
    app: AppSession,
    ctx: PlayContext,
    user_message: str,
    answer: str,
) -> list[dict[str, str]]:
    messages = messages_for_context(app, ctx)
    messages.append({"role": "user", "content": user_message})
    messages.append({"role": "assistant", "content": answer})
    sync_messages(app, ctx, messages)
    return messages
