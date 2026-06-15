"""AI journal prose for Outgunned (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.games.outgunned.character import OutgunnedHero
from src.games.outgunned.lonelog import log_narrative_line, narrative_context_for_ai
from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    mechanics: str,
    *,
    entity: OutgunnedHero | None = None,
    chat_provider: ChatProvider = "ollama",
) -> str | None:
    llm = get_langchain_chat_llm(chat_provider)
    hero = entity
    who = (hero.name if hero else "") or "the solo hero"
    mission = (hero.mission_title if hero else "") or "the mission"
    story_so_far = ""
    if hero and hero.id:
        story_so_far = narrative_context_for_ai(hero.id)
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing an action-movie scene for Outgunned solo play.
Write in first person past tense as {who}, on mission: {mission}.
Use 2–3 short paragraphs inspired by the mechanical prompts below.
Tone: cinematic, high-octane, 90s action film. Build on prior events when given.
Do not explain rules or dice. Plain prose only.

{prior}
Scene mechanics:
{mechanics[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write evocative solo action-movie prose for a tabletop RPG."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    prose = text.strip()
    if prose and hero and hero.id:
        try:
            summary = synthesize_lonelog_summary(prose, chat_provider=chat_provider)
            if summary:
                log_narrative_line(hero.id, summary)
        except Exception:
            pass
    return prose or None


def synthesize_lonelog_summary(
    prose: str,
    *,
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""Summarize this Outgunned action scene in 1–2 short sentences for a session log.
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
