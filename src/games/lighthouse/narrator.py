"""AI logbook prose for Lighthouse (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_logbook_entry(
    context: str,
    *,
    keeper_name: str = "",
    night: int = 1,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    who = keeper_name.strip() or "the keeper"
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a logbook entry for "The Lighthouse at the Edge of the Universe".
Write in first person past tense as {who}, night {night} on the edge of the universe.
Use 2–4 short paragraphs inspired by the mechanical prompt below.
Tone: reflective, meditative, slightly uncanny, intimate.
Build on prior logbook events when given. Do not explain rules or dice/cards. Plain prose only.

{prior}
Tonight's prompt:
{context[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write evocative solo journaling prose for a tabletop RPG."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return text.strip()


def synthesize_lonelog_summary(
    prose: str,
    *,
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""Summarize this lighthouse logbook entry in 1–2 short sentences for a session log.
Past tense, in-world. No card names or rulebook language.

{prose[:4000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write a very concise in-world summary."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return text.strip()
