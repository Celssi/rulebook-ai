"""AI scene prose for Cosmere (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.games.cosmere.entity import CosmereCharacter
from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    mechanics: str,
    *,
    entity: CosmereCharacter,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    who = entity.name.strip() or "the character"
    path_role = f"{entity.path} {entity.role}".strip() or "adventurer"
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are the Game Master for a Cosmere RPG solo session on Roshar.
Write 2–4 short paragraphs in third person past tense for {who} ({path_role}).
Use the mechanical results below; do not explain dice or rules. Plain prose only.

{prior}
Mechanics:
{mechanics[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write evocative GM narration for a tabletop RPG."),
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
    prompt = f"""Summarize this Cosmere scene in 1–2 short sentences for a session log.
Past tense, in-world. No rulebook language.

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
