"""AI journal prose for Ashes (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    context: str,
    *,
    scion_name: str = "",
    scion_class: str = "",
    rooms_cleared: int = 0,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    who = scion_name.strip() or "the Scion"
    role = f", a {scion_class.strip()}" if scion_class.strip() else ""
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a solo dungeon journal entry for Ashes (Mayfalls).
Write in first person past tense as {who}{role}. Use 2–4 short paragraphs inspired by the room and prompt.
Tone: dark fantasy, perilous ruins, personal stakes. Build on prior events when given.
Do not explain rules or list mechanics. No bullet lists. Plain prose only.

Rooms cleared this run: {rooms_cleared}
{prior}
Today's draw:
{context[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write rich solo-journaling prose for a dungeon-crawl RPG."),
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
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""Summarize this Ashes journal entry in 1–2 short sentences for a session log.
Past tense, in-world. No card names or rulebook language.

{journal_prose[:4000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write a compact session-log summary."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return text.strip()
