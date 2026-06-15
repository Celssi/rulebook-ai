"""AI journal prose for Apothecaria (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    context: str,
    *,
    witch_name: str = "",
    week: int = 1,
    season: str = "spring",
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    """Return 2–4 short paragraphs of first-person journal prose for chat."""
    llm = get_langchain_chat_llm(chat_provider)
    who = witch_name.strip() or "the village witch"
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a solo journal entry for "Apothecaria" — a village witch curing ailments in High Rannoc.
Write in first person past tense as {who}. Use 2–4 short paragraphs inspired by the prompt below.
Tone: warm, folkloric, practical, with quiet wonder — a witch's cottage journal, not a rulebook.
Build on prior journal events when given. Do not explain rules, list reagents mechanically, or say "based on context".
No bullet lists. Plain prose only (no Lonelog prefix).

Week {week} of {season}.
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
    """Return 1–2 sentences for Lonelog => lines."""
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""Summarize this Apothecaria journal entry in 1–2 short sentences for a session log.
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
