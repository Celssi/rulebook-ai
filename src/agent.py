"""LangGraph agent: route questions to RAG or game-specific tools."""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.config import DEFAULT_GAME_ID
from src.llm import ChatProvider, get_langchain_chat_llm
from src.games.brambletrek.agent import brambletrek_multi_node
from src.games.brambletrek.character import character_from_dict
from src.games.registry import get_game_plugin
from src.games.warhammer_40k import retrieval as r40k
from src.games.warhammer_40k.state import GameState
from src.prompts import build_system_prompt, detect_language, tool_output_instructions
from src.tools import (
    draw_cards,
    extract_dice_expression,
    format_card_result,
    format_dice_result,
    is_ai_draw_request,
    is_card_plus_rules_question,
    is_card_question,
    is_dice_question,
    is_physical_card_report,
    list_leviathan_units,
    normalize_card_name,
    register_physical_card,
    reset_deck,
    roll_dice,
    search_rules,
)


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    route: str
    tool_output: str
    sources: list[dict]
    language: str
    game_state: GameState | None
    retrieval: dict
    game_id: str
    shortcut_id: str
    brambletrek_character: dict | None
    chat_provider: ChatProvider
    char_id: str | None
    story_mode: str
    card_source: str


def _last_user_text(state: AgentState) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _bt_character(state: AgentState):
    data = state.get("brambletrek_character")
    return character_from_dict(data) if data else None


def _format_sources(sources: list[dict], limit: int = 5) -> str:
    return "\n".join(
        f"- {s.get('source_label')} p.{s.get('page')} ({s.get('faction')})"
        for s in sources[:limit]
    )


def router_node(state: AgentState) -> dict:
    text = _last_user_text(state)
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    card_source = state.get("card_source", "virtual")
    plugin = get_game_plugin(game_id)
    game_route = plugin.route_before_generic(
        text,
        brambletrek_character=state.get("brambletrek_character"),
    )
    if game_route:
        return game_route
    if is_dice_question(text):
        route = "dice"
    elif is_card_plus_rules_question(text):
        route = "card_rag"
    elif card_source == "physical" and (
        is_physical_card_report(text) or normalize_card_name(text)
    ):
        route = "physical_card"
    elif is_card_question(text) and (card_source != "physical" or is_ai_draw_request(text)):
        route = "cards"
    elif any(
        w in text.lower()
        for w in (
            "hello",
            "thanks",
            "who are you",
        )
    ) and len(text.split()) < 8:
        route = "chat"
    else:
        route = "rag"
    return {"route": route, "language": detect_language(text)}


def leviathan_node(state: AgentState) -> dict:
    text = _last_user_text(state).lower()
    side: Literal["space_marines", "tyranids", "both"] = "both"
    if any(w in text for w in ("tyranid", "nids", "hive", "gaunt", "synapse")):
        side = "tyranids"
    elif any(
        w in text
        for w in ("space marine", "astartes", "sm ", "terminator captain", "dreadnought")
    ):
        side = "space_marines"
    output = list_leviathan_units(side)
    return {"tool_output": output, "sources": []}


def dice_node(state: AgentState) -> dict:
    text = _last_user_text(state)
    expr = extract_dice_expression(text) or "d6"
    result = roll_dice(expr)
    return {"tool_output": format_dice_result(result), "sources": []}


def cards_node(state: AgentState) -> dict:
    text = _last_user_text(state).lower()
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    char_id = state.get("char_id")

    if any(w in text for w in ("reset", "reshuffle", "new deck", "shuffle")):
        result = reset_deck(game_id=game_id, char_id=char_id)
        return {"tool_output": format_card_result(result), "sources": []}

    count = 1
    for token in text.replace(",", " ").split():
        if token.isdigit():
            count = min(max(int(token), 1), 52)
            break
    result = draw_cards(count=count, game_id=game_id, char_id=char_id)
    return {"tool_output": format_card_result(result), "sources": []}


def physical_card_node(state: AgentState) -> dict:
    text = _last_user_text(state)
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    char_id = state.get("char_id")
    result = register_physical_card(text, game_id=game_id, char_id=char_id)
    return {"tool_output": format_card_result(result), "sources": []}


def card_rag_node(state: AgentState) -> dict:
    """Draw a card, then look up table meaning in indexed rules."""
    text = _last_user_text(state)
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    char_id = state.get("char_id")
    card_source = state.get("card_source", "virtual")
    retrieval_cfg = state.get("retrieval") or {}

    if any(w in text.lower() for w in ("reset", "reshuffle", "new deck")):
        result = reset_deck(game_id=game_id, char_id=char_id)
        return {"tool_output": format_card_result(result), "sources": []}

    draw_summary = ""
    if card_source == "physical":
        card = normalize_card_name(text)
        if not card:
            return {
                "tool_output": "Report the physical card you drew (e.g. Queen of Hearts).",
                "sources": [],
            }
        reg = register_physical_card(text, game_id=game_id, char_id=char_id)
        if not reg.get("ok"):
            return {"tool_output": format_card_result(reg), "sources": []}
        draw_summary = format_card_result(reg)
        card = reg["cards"][0]
    else:
        draw = draw_cards(count=1, game_id=game_id, char_id=char_id)
        if not draw.get("ok"):
            return {"tool_output": format_card_result(draw), "sources": []}
        card = draw["cards"][0]
        draw_summary = format_card_result(draw)
    rules_q = (
        f"{text}\n\nDrawn card: {card}. "
        "Explain what this means using the rules tables (reason for adventure, background, etc.)."
    )
    result = search_rules(
        rules_q,
        game_state=state.get("game_state"),
        game_id=game_id,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=bool(retrieval_cfg.get("use_hybrid", True)),
        use_rerank=bool(retrieval_cfg.get("use_rerank", False)),
        brambletrek_character=_bt_character(state),
        chat_provider=state.get("chat_provider", "ollama"),
    )
    tool_output = (
        f"{draw_summary}\n\n{result['answer']}\n\nSources:\n{_format_sources(result['sources'])}"
    )
    return {
        "tool_output": tool_output,
        "sources": result["sources"],
        "language": result["language"],
    }


def _factions_for_rag(
    text: str,
    game: GameState | None,
    game_id: str,
) -> list[str] | None:
    plugin = get_game_plugin(game_id)
    if not plugin.has_game_state:
        return None
    return r40k.infer_factions_from_text(text, game)


def rag_node(state: AgentState) -> dict:
    text = _last_user_text(state)
    game = state.get("game_state")
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    factions = _factions_for_rag(text, game, game_id)
    retrieval_cfg = state.get("retrieval") or {}

    result = search_rules(
        text,
        factions=factions,
        game_state=game,
        game_id=game_id,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=bool(retrieval_cfg.get("use_hybrid", True)),
        use_rerank=bool(retrieval_cfg.get("use_rerank", False)),
        brambletrek_character=_bt_character(state),
        chat_provider=state.get("chat_provider", "ollama"),
    )
    tool_output = f"{result['answer']}\n\nSources:\n{_format_sources(result['sources'])}"
    return {
        "tool_output": tool_output,
        "sources": result["sources"],
        "language": result["language"],
    }


def chat_node(state: AgentState) -> dict:
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    out = get_game_plugin(game_id).chat_greeting()
    return {"tool_output": out, "sources": []}


_DIRECT_ROUTES = frozenset(
    {
        "rag",
        "leviathan",
        "chat",
        "dice",
        "cards",
        "physical_card",
        "card_rag",
        "brambletrek_multi",
    }
)


def synthesize_node(state: AgentState) -> dict:
    if state.get("route") in _DIRECT_ROUTES:
        tool_output = state.get("tool_output", "").strip()
        if tool_output:
            return {"messages": [AIMessage(content=tool_output)]}

    lang = state.get("language") or "en"
    system = build_system_prompt(
        lang,
        game=state.get("game_state"),
        game_id=state.get("game_id", DEFAULT_GAME_ID),
        brambletrek_character=_bt_character(state),
        story_mode=state.get("story_mode", "player"),
        card_source=state.get("card_source", "virtual"),
    )
    llm = get_langchain_chat_llm(state.get("chat_provider", "ollama"))

    user_q = _last_user_text(state)
    tool_hint = tool_output_instructions(state.get("route", ""))
    prompt = f"""The user asked: {user_q}

Tool result:
{state.get('tool_output', '')}

{tool_hint}

Synthesize a clear, helpful final answer for the player. Keep citations from the tool result.
If the tool already gave a complete answer, you may repeat it with light editing."""

    response = llm.invoke(
        [
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ]
    )
    return {"messages": [AIMessage(content=response.content)]}


def route_decision(state: AgentState) -> str:
    return state.get("route", "rag")


def build_agent():
    graph = StateGraph(AgentState)
    graph.add_node("router", router_node)
    graph.add_node("leviathan", leviathan_node)
    graph.add_node("dice", dice_node)
    graph.add_node("cards", cards_node)
    graph.add_node("physical_card", physical_card_node)
    graph.add_node("brambletrek_multi", brambletrek_multi_node)
    graph.add_node("card_rag", card_rag_node)
    graph.add_node("rag", rag_node)
    graph.add_node("chat", chat_node)
    graph.add_node("synthesize", synthesize_node)

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        route_decision,
        {
            "leviathan": "leviathan",
            "dice": "dice",
            "cards": "cards",
            "physical_card": "physical_card",
            "card_rag": "card_rag",
            "brambletrek_multi": "brambletrek_multi",
            "rag": "rag",
            "chat": "chat",
        },
    )
    graph.add_edge("leviathan", "synthesize")
    graph.add_edge("dice", "synthesize")
    graph.add_edge("cards", "synthesize")
    graph.add_edge("physical_card", "synthesize")
    graph.add_edge("brambletrek_multi", "synthesize")
    graph.add_edge("card_rag", "synthesize")
    graph.add_edge("rag", "synthesize")
    graph.add_edge("chat", "synthesize")
    graph.add_edge("synthesize", END)

    return graph.compile()


def run_agent(
    question: str,
    history: list[BaseMessage] | None = None,
    game_state: GameState | None = None,
    game_id: str = DEFAULT_GAME_ID,
    retrieval: dict | None = None,
    brambletrek_character: dict | None = None,
    chat_provider: ChatProvider = "ollama",
    char_id: str | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> dict:
    """Run agent and return final answer + sources."""
    app = build_agent()
    messages: list[BaseMessage] = list(history or [])
    messages.append(HumanMessage(content=question))
    final = app.invoke(
        {
            "messages": messages,
            "route": "",
            "tool_output": "",
            "sources": [],
            "language": detect_language(question),
            "game_state": game_state,
            "game_id": game_id,
            "retrieval": retrieval or {},
            "shortcut_id": "",
            "brambletrek_character": brambletrek_character,
            "chat_provider": chat_provider,
            "char_id": char_id,
            "story_mode": story_mode,
            "card_source": card_source,
        }
    )
    last_ai = ""
    for msg in reversed(final["messages"]):
        if isinstance(msg, AIMessage):
            last_ai = msg.content if isinstance(msg.content, str) else str(msg.content)
            break
    return {
        "answer": last_ai,
        "sources": final.get("sources", []),
        "language": final.get("language", detect_language(question)),
        "route": final.get("route", ""),
    }
