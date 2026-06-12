"""Chat LLM factory: Ollama (local) or Claude (Anthropic cloud)."""

from __future__ import annotations

import os
from typing import Literal

from src.settings import (
    ANTHROPIC_API_KEY,
    CHAT_MODEL,
    CLAUDE_CHAT_MODEL,
    OLLAMA_BASE_URL,
    OLLAMA_REQUEST_TIMEOUT,
)

ChatProvider = Literal["ollama", "claude"]

_PROVIDER_LABELS: dict[ChatProvider, str] = {
    "ollama": "Ollama (local)",
    "claude": "Claude (cloud)",
}


def resolve_anthropic_api_key(*, anthropic_key: str | None = None) -> str | None:
    """Return API key from explicit override, env, or settings."""
    if anthropic_key and anthropic_key.strip():
        return anthropic_key.strip()
    env_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if env_key:
        return env_key
    return ANTHROPIC_API_KEY


def available_chat_providers(*, anthropic_key: str | None = None) -> list[ChatProvider]:
    providers: list[ChatProvider] = ["ollama"]
    if resolve_anthropic_api_key(anthropic_key=anthropic_key):
        providers.append("claude")
    return providers


def provider_display_name(provider: ChatProvider) -> str:
    return _PROVIDER_LABELS[provider]


def active_model_name(provider: ChatProvider) -> str:
    if provider == "claude":
        return CLAUDE_CHAT_MODEL
    return CHAT_MODEL


def get_llamaindex_chat_llm(provider: ChatProvider = "ollama", *, api_key: str | None = None):
    if provider == "claude":
        from llama_index.llms.anthropic import Anthropic

        key = resolve_anthropic_api_key(anthropic_key=api_key)
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude chat provider")
        return Anthropic(model=CLAUDE_CHAT_MODEL, api_key=key)

    from llama_index.llms.ollama import Ollama

    return Ollama(
        model=CHAT_MODEL,
        base_url=OLLAMA_BASE_URL,
        request_timeout=OLLAMA_REQUEST_TIMEOUT,
    )


def get_langchain_chat_llm(provider: ChatProvider = "ollama", *, api_key: str | None = None):
    if provider == "claude":
        from langchain_anthropic import ChatAnthropic

        key = resolve_anthropic_api_key(anthropic_key=api_key)
        if not key:
            raise ValueError("ANTHROPIC_API_KEY is required for Claude chat provider")
        return ChatAnthropic(model=CLAUDE_CHAT_MODEL, api_key=key, temperature=0.2)

    from langchain_ollama import ChatOllama

    return ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.2)
