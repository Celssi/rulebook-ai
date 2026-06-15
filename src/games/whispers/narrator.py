"""AI journal prose for Whispers in the Walls (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    context: str,
    *,
    investigator_name: str = "",
    location_name: str = "",
    turn_number: int = 1,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    who = investigator_name.strip() or "the private investigator"
    loc = location_name.strip() or "the haunted room"
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a solo horror journal entry for "Whispers in the Walls".
Write in first person past tense as {who}, investigating {loc}. Use 2–4 short paragraphs inspired by the prompt.
Tone: investigative, dark, body-horror-tinged but not gratuitous. Build on prior events when given.
Do not explain rules or list mechanics. Plain prose only.

Turn: {turn_number}
{prior}
Today's prompt:
{context[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write rich solo horror journaling prose for a tabletop RPG."),
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
    prompt = f"""Summarize this Whispers in the Walls journal entry in 1–2 short sentences for a session log.
Past tense, in-world. No card names or rulebook language.

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
