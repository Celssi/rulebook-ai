"""AI scene prose for MLP (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.games.mlp.entity import MlpPony
from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    mechanics: str,
    *,
    entity: MlpPony,
    story_so_far: str = "",
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    who = entity.pony_name.strip() or entity.name.strip() or "the pony"
    origin = entity.origin.replace("_", " ") if entity.origin else "pony"
    role = entity.role.replace("spirit_of_", "").replace("_", " ") if entity.role else ""
    role_note = f", Spirit of {role.title()}" if role else ""
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are the Game Master for a My Little Pony RPG solo session in Equestria.
Write 2–4 short paragraphs in third person past tense for {who}, an {origin}{role_note}.
Tone: warm, adventurous, friendship-focused. Use the mechanics below; no rule explanations.

{prior}
Mechanics:
{mechanics[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write wholesome GM narration for a family-friendly RPG."),
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
    prompt = f"""Summarize this MLP scene in 1–2 short sentences for a session log.
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
