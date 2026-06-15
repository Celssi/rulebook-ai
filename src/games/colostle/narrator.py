"""AI journal prose for Colostle (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    mechanics: str,
    *,
    adventurer_name: str,
    chapter: int,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    who = adventurer_name.strip() or "the adventurer"
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a journal entry for the Colostle solo RPG.
Write in first person past tense as {who}, chapter {chapter} in the Roomlands.
Use 2–4 short paragraphs inspired by the mechanical prompts below.
Tone: mythic, personal, adventurous. Build on prior events when given.
Do not explain rules or card names. Plain prose only.

{prior}
Today's draws:
{mechanics[:3000]}
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
    prompt = f"""Summarize this Colostle journal entry in 1–2 short sentences for a session log.
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
