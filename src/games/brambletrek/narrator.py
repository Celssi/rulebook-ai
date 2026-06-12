"""AI narrator lines for Lonelog (ai_narrator story mode)."""

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from src.llm import ChatProvider, get_langchain_chat_llm


def synthesize_narrator_line(
    context: str,
    *,
    chat_provider: ChatProvider = "ollama",
) -> str:
    """Return 1–3 sentences of in-world consequence for Lonelog => lines."""
    llm = get_langchain_chat_llm(chat_provider)
    prompt = f"""You are narrating a Brambletrek solo RPG session.
Given the mechanical outcome below, write 1–3 short sentences of in-world consequence.
Do not repeat dice numbers or card names unless essential. No bullet lists.
Output plain prose only (no Lonelog prefix).

Mechanical context:
{context[:3000]}
"""
    response = llm.invoke(
        [
            SystemMessage(content="Write concise tabletop narrative prose."),
            HumanMessage(content=prompt),
        ]
    )
    text = response.content if isinstance(response.content, str) else str(response.content)
    return text.strip()
