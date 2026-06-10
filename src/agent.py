"""LangGraph agent: route questions to RAG or Leviathan list tools."""

from __future__ import annotations

from typing import Annotated, Literal, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from src.config import CHAT_MODEL, DEFAULT_GAME_ID, GAME_40K, GAME_BRAMBLETREK, OLLAMA_BASE_URL
from src.brambletrek_actions import match_brambletrek_shortcut, run_shortcut
from src.brambletrek_character import character_from_dict
from src.prompts import build_system_prompt, detect_language, tool_output_instructions
from src.tools import (
    draw_cards,
    extract_dice_expression,
    format_card_result,
    format_dice_result,
    is_card_plus_rules_question,
    is_card_question,
    is_dice_question,
    is_leviathan_list_question,
    list_leviathan_units,
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


_MULTI_DRAW_SHORTCUTS = frozenset(
    {
        "journey_day",
        "aldwund_day",
        "adventure_scene",
        "combat_setup",
        "resources",
        "random_character",
        "overcome_odds",
    }
)


def _last_user_text(state: AgentState) -> str:
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            return msg.content if isinstance(msg.content, str) else str(msg.content)
    return ""


def _bt_character(state: AgentState):
    data = state.get("brambletrek_character")
    return character_from_dict(data) if data else None


def router_node(state: AgentState) -> dict:
    text = _last_user_text(state)
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    if game_id == GAME_BRAMBLETREK:
        bt = _bt_character(state)
        shortcut_id = match_brambletrek_shortcut(
            text,
            active_adventure=bt.active_adventure if bt else "",
        )
        if shortcut_id in _MULTI_DRAW_SHORTCUTS:
            return {
                "route": "brambletrek_multi",
                "shortcut_id": shortcut_id,
                "language": detect_language(text),
            }
        if shortcut_id == "start_playing":
            return {"route": "rag", "language": detect_language(text)}
    if game_id == GAME_40K and is_leviathan_list_question(text):
        route = "leviathan"
    elif is_dice_question(text):
        route = "dice"
    elif is_card_plus_rules_question(text):
        route = "card_rag"
    elif is_card_question(text):
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

    if any(w in text for w in ("reset", "reshuffle", "new deck", "shuffle")):
        result = reset_deck(game_id=game_id)
        return {"tool_output": format_card_result(result), "sources": []}

    count = 1
    for token in text.replace(",", " ").split():
        if token.isdigit():
            count = min(max(int(token), 1), 52)
            break
    result = draw_cards(count=count, game_id=game_id)
    return {"tool_output": format_card_result(result), "sources": []}


def brambletrek_multi_node(state: AgentState) -> dict:
    """Pre-draw cards for a Brambletrek shortcut, then look up table meanings."""
    game_id = state.get("game_id", GAME_BRAMBLETREK)
    shortcut_id = state.get("shortcut_id") or "journey_day"
    retrieval_cfg = state.get("retrieval") or {}

    bt = _bt_character(state)
    run = run_shortcut(
        shortcut_id,
        game_id=game_id,
        in_aldwund=bool(bt and bt.in_aldwund),
        reason_band=bt.reason_band if bt else "",
        active_adventure=bt.active_adventure if bt else "",
    )
    if shortcut_id in ("journey_day", "aldwund_day"):
        top_k = 12
    elif shortcut_id == "adventure_scene":
        top_k = 14
    else:
        top_k = 10
    result = search_rules(
        run["prompt"],
        game_state=state.get("game_state"),
        game_id=game_id,
        top_k=top_k,
        candidate_k=retrieval_cfg.get("candidate_k"),
        use_hybrid=bool(retrieval_cfg.get("use_hybrid", True)),
        brambletrek_character=_bt_character(state),
    )
    source_summary = "\n".join(
        f"- {s.get('source_label')} p.{s.get('page')} ({s.get('faction')})"
        for s in result["sources"][:5]
    )
    tool_output = (
        f"{run['user_message']}\n\n{result['answer']}\n\nSources:\n{source_summary}"
    )
    return {
        "tool_output": tool_output,
        "sources": result["sources"],
        "language": result["language"],
    }


def card_rag_node(state: AgentState) -> dict:
    """Draw a card, then look up table meaning in indexed rules."""
    text = _last_user_text(state)
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    retrieval_cfg = state.get("retrieval") or {}

    if any(w in text.lower() for w in ("reset", "reshuffle", "new deck")):
        result = reset_deck(game_id=game_id)
        return {"tool_output": format_card_result(result), "sources": []}

    draw = draw_cards(count=1, game_id=game_id)
    if not draw.get("ok"):
        return {"tool_output": format_card_result(draw), "sources": []}

    card = draw["cards"][0]
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
        brambletrek_character=_bt_character(state),
    )
    source_summary = "\n".join(
        f"- {s.get('source_label')} p.{s.get('page')} ({s.get('faction')})"
        for s in result["sources"][:5]
    )
    tool_output = (
        f"{format_card_result(draw)}\n\n{result['answer']}\n\nSources:\n{source_summary}"
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
    if game_id != GAME_40K:
        return None
    if game and game.my_army:
        return game.factions_for_retrieval()
    lower = text.lower()
    if any(w in lower for w in ("tyranid", "synapse", "norn", "hormagaunt", "termagant")):
        return ["tyranids", "cards_nids", "core"]
    if any(w in lower for w in ("space marine", "astartes", "oath", "terminator", "dreadnought")):
        return ["space_marines", "cards_sm", "core"]
    if any(w in lower for w in ("core", "phase", "fight", "shoot", "move", "charge")):
        return ["core"]
    return None


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
        brambletrek_character=_bt_character(state),
    )
    source_summary = "\n".join(
        f"- {s.get('source_label')} p.{s.get('page')} ({s.get('faction')})"
        for s in result["sources"][:5]
    )
    tool_output = f"{result['answer']}\n\nSources:\n{source_summary}"
    return {
        "tool_output": tool_output,
        "sources": result["sources"],
        "language": result["language"],
    }


def chat_node(state: AgentState) -> dict:
    game_id = state.get("game_id", DEFAULT_GAME_ID)
    if game_id == GAME_40K:
        out = (
            "I'm your Warhammer 40k rules assistant. Ask about rules, units, or "
            "what's in the Leviathan box — I'll search your indexed documents. "
            "You can also roll dice (e.g. roll 2d6) or draw cards."
        )
    else:
        out = (
            "I'm your Brambletrek rules assistant. Ask about rules or what dice "
            "results mean, and I'll answer from your indexed books. "
            "You can also roll dice or draw cards from the table deck."
        )
    return {"tool_output": out, "sources": []}


def synthesize_node(state: AgentState) -> dict:
    # Avoid a second LLM call for tool-based routes; tool output is already formatted.
    if state.get("route") in {"rag", "leviathan", "chat", "dice", "cards", "card_rag", "brambletrek_multi"}:
        tool_output = state.get("tool_output", "").strip()
        if tool_output:
            return {"messages": [AIMessage(content=tool_output)]}

    lang = state.get("language") or "en"
    system = build_system_prompt(
        lang,
        game=state.get("game_state"),
        game_id=state.get("game_id", DEFAULT_GAME_ID),
        brambletrek_character=_bt_character(state),
    )
    llm = ChatOllama(model=CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=0.2)

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
            "card_rag": "card_rag",
            "brambletrek_multi": "brambletrek_multi",
            "rag": "rag",
            "chat": "chat",
        },
    )
    graph.add_edge("leviathan", "synthesize")
    graph.add_edge("dice", "synthesize")
    graph.add_edge("cards", "synthesize")
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
