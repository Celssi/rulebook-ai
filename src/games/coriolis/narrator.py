"""AI scene prose for Coriolis: The Great Dark (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.games.coriolis.character import CoriolisExplorer
from src.games.coriolis.lonelog import log_narrative_line, narrative_context_for_ai
from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_journal_entry(
    mechanics: str,
    *,
    entity: CoriolisExplorer | None = None,
    chat_provider: ChatProvider = "ollama",
) -> str | None:
    llm = get_langchain_chat_llm(chat_provider)
    crew = entity
    who = (crew.name if crew else "") or "the Explorer"
    bird = (crew.bird_name if crew else "") or "the Bird"
    crew_label = (crew.crew_name if crew else "") or "the crew"
    story_so_far = ""
    if crew and crew.id:
        story_so_far = narrative_context_for_ai(crew.id)
    prior = ""
    if story_so_far.strip():
        prior = f"\n\n{story_so_far.strip()[:3500]}\n"
    prompt = f"""You are writing a scene for Coriolis: The Great Dark solo play in the Lost Horizon.
Write in first person past tense as {who} of {crew_label} with Bird {bird}.
Use 2–3 short paragraphs inspired by the mechanics below.
Tone: islamic sci-fi exploration, Blight and Builder ruins, Guild intrigue. Plain prose only.

{prior}
Scene mechanics:
{mechanics[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write evocative solo space-opera prose for a tabletop RPG."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    prose = text.strip()
    if prose and crew and crew.id:
        try:
            summary = synthesize_lonelog_summary(prose, chat_provider=chat_provider)
            if summary:
                log_narrative_line(crew.id, summary)
        except Exception:
            pass
    return prose or None


def synthesize_lonelog_summary(
    prose: str,
    *,
    chat_provider: ChatProvider = "ollama",
) -> str:
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""Summarize this Coriolis scene in 1–2 short sentences for a session log.
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
