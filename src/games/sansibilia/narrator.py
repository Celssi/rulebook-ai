"""AI journal prose for San Sibilia (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    context: str,
    *,
    visit_name: str = "",
    archetype: str = "",
    visit_day: int = 1,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    """Return 2–4 short paragraphs of first-person journal prose for chat."""
    llm = get_langchain_chat_llm(chat_provider)
    who = visit_name.strip() or "the visitor"
    role = f" ({archetype.strip()})" if archetype.strip() else ""
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a solo journal entry for "A Visit to San Sibilia".
Write in first person past tense as {who}{role}. Use 2–4 short paragraphs inspired by today's prompt.
Match the zine's tone: reflective, evocative, slightly uncanny, grounded in the city.
Build on prior journal events when given — keep names, places, and tone consistent.
Do not explain rules or list mechanics. No bullet lists. Plain prose only (no Lonelog prefix).

Journal day: {visit_day}
{prior}
Today's prompt:
{context[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write rich solo-journaling prose for a tabletop RPG."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return text.strip()


def synthesize_lonelog_summary(
    journal_prose: str,
    *,
    chat_provider: ChatProvider = "ollama",
) -> str:
    """Return 1–2 sentences for Lonelog => lines (not the full journal)."""
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""Summarize this San Sibilia journal entry in 1–2 short sentences for a tabletop session log.
Past tense, in-world. No card names, ranks, suits, or rulebook language. Plain prose only.

{journal_prose[:4000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write a very concise in-world summary."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return text.strip()
