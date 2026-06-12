"""Streamlit UI for rulebook-ai."""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.components.shared import (
    FACTION_LABELS,
    MEMORY_MESSAGES,
    RETRIEVAL_PROFILES,
    deck_key,
    recent_chat_history,
    refresh_deck,
    render_deck_sidebar,
    render_index_section,
    render_sources_sidebar,
    sync_deck,
    to_langchain_history,
)
from app.games import brambletrek as bt_ui
from app.games import warhammer_40k as wh40k_ui
from src.agent import run_agent
from src.config import DEFAULT_GAME_ID, EMBED_MODEL, GAME_BRAMBLETREK, get_all_factions, get_game_config
from src.games.registry import game_options, get_game_plugin
from src.games.saves import get_play_store, slot_entity_key
from src.llm import (
    ChatProvider,
    active_model_name,
    available_chat_providers,
    provider_display_name,
)
from src.rag import index_exists, query as rag_query
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
    normalize_card_name,
    register_physical_card,
    run_explicit_command,
)


def _resolve_anthropic_key() -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if key:
        return key
    try:
        key = (st.secrets.get("ANTHROPIC_API_KEY") or "").strip()
    except Exception:
        key = ""
    if key:
        os.environ.setdefault("ANTHROPIC_API_KEY", key)
        return key
    return None


def _deck_char_id(game_id: str) -> str | None:
    store = get_play_store(game_id)
    if store:
        sid = store.active_slot_id(st)
        return sid or None
    return None


def _slot_entity_dict(game_id: str) -> dict | None:
    store = get_play_store(game_id)
    if not store:
        return None
    return st.session_state.get(slot_entity_key(game_id))


def _play_settings(game_id: str) -> tuple[str, str]:
    store = get_play_store(game_id)
    if not store:
        return "player", "virtual"
    s = store.get_settings(st)
    return s.get("story_mode", "player"), s.get("card_source", "virtual")


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    if "selected_game_id" not in st.session_state:
        st.session_state.selected_game_id = DEFAULT_GAME_ID
    if "chat_provider" not in st.session_state:
        st.session_state.chat_provider = "ollama"
    _resolve_anthropic_key()
    wh40k_ui.init_session_game_state()
    bt_ui.init_session_character()
    for gid in game_options():
        if gid == GAME_BRAMBLETREK:
            continue
        key = deck_key(gid)
        if key not in st.session_state:
            st.session_state[key] = None


def _answer_user_prompt(
    prompt: str,
    *,
    mode: str,
    game_id: str,
    game_state,
    prior_history: list[dict[str, str]],
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider,
) -> tuple[str, list[dict], str]:
    char_id = _deck_char_id(game_id)
    sync_deck(game_id, char_id)

    if plugin := get_game_plugin(game_id):
        if plugin.has_character_sheet and char_id:
            bt_ui.log_user_prompt(char_id, prompt)

    store = get_play_store(game_id)

    cmd = run_explicit_command(prompt, game_id=game_id, char_id=char_id)
    if cmd is not None:
        if cmd.get("route") == "log" and char_id and store:
            store.append_log(char_id, cmd.get("log_text", ""), st=st)
        tr = cmd.get("tool_result")
        if char_id and tr and store:
            if cmd.get("route") == "dice" and tr.get("ok"):
                store.log_roll(char_id, "", result=tr, st=st)
            elif cmd.get("route") == "cards" and tr.get("ok") and tr.get("cards"):
                store.log_draw(char_id, tr["cards"], st=st)
        refresh_deck(game_id, char_id)
        return cmd.get("answer", ""), cmd.get("sources", []), cmd.get("route", "command")

    plugin = get_game_plugin(game_id)
    story_mode, card_source = _play_settings(game_id)

    if plugin.has_character_sheet:
        handled = bt_ui.try_handle_prompt(
            prompt,
            mode=mode,
            game_id=game_id,
            prior_history=prior_history,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
            chat_provider=chat_provider,
        )
        if handled is not None:
            refresh_deck(game_id, char_id)
            return handled

    if mode == "Agent":
        out = run_agent(
            prompt,
            history=to_langchain_history(prior_history),
            game_state=game_state,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=_slot_entity_dict(game_id),
            chat_provider=chat_provider,
            char_id=char_id,
            story_mode=story_mode,
            card_source=card_source,
        )
        refresh_deck(game_id, char_id)
        return out["answer"], out.get("sources", []), out.get("route", "")

    if is_card_plus_rules_question(prompt):
        out = run_agent(
            prompt,
            history=to_langchain_history(prior_history),
            game_state=game_state,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=_slot_entity_dict(game_id),
            chat_provider=chat_provider,
            char_id=char_id,
            story_mode=story_mode,
            card_source=card_source,
        )
        refresh_deck(game_id, char_id)
        return out["answer"], out.get("sources", []), out.get("route", "card_rag")

    if is_dice_question(prompt):
        expr = extract_dice_expression(prompt) or "d6"
        result = roll_dice(expr)
        if char_id and result.get("ok") and store:
            store.log_roll(char_id, "", result=result, st=st)
        return format_dice_result(result), [], "dice"

    if is_card_question(prompt):
        if card_source == "physical" and not is_ai_draw_request(prompt):
            if normalize_card_name(prompt) or is_physical_card_report(prompt):
                result = register_physical_card(prompt, game_id=game_id, char_id=char_id)
                if char_id and result.get("ok") and result.get("cards") and store:
                    store.log_draw(char_id, result["cards"], label="Physical draw", st=st)
            else:
                return (
                    "Physical deck mode: draw from your real deck and report the card "
                    "(e.g. Queen of Hearts), or ask to 'draw a card for me' for a virtual draw.",
                    [],
                    "cards",
                )
        else:
            result = draw_cards(count=1, game_id=game_id, char_id=char_id)
            if char_id and result.get("ok") and result.get("cards") and store:
                store.log_draw(char_id, result["cards"], st=st)
        refresh_deck(game_id, char_id)
        return format_card_result(result), [], "cards"

    factions = selected_factions if selected_factions else None
    bt_char = bt_ui.get_bt_character() if plugin.has_character_sheet else None
    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions,
        game_state=game_state,
        game_id=game_id,
        chat_history=prior_history,
        candidate_k=retrieval_cfg["candidate_k"],
        use_hybrid=retrieval_cfg["use_hybrid"],
        brambletrek_character=bt_char,
        chat_provider=chat_provider,
    )
    return result.answer, result.sources, "rag"


st.set_page_config(
    page_title="rulebook-ai",
    page_icon="⚔️",
    layout="wide",
)

_init_session()
GAME_OPTIONS = game_options()

selected_game_id = st.session_state.selected_game_id
selected_game = get_game_config(selected_game_id)
plugin = get_game_plugin(selected_game_id)

st.title(f"{selected_game['label']} – rulebook-ai")
if plugin.has_game_state:
    wh40k_ui.render_header()
    game_state = wh40k_ui.get_game_state()
else:
    bt_ui.render_header()
    game_state = None

with st.sidebar:
    st.header("Settings")
    chosen_game = st.selectbox(
        "Game",
        options=list(GAME_OPTIONS.keys()),
        index=list(GAME_OPTIONS.keys()).index(st.session_state.selected_game_id),
        format_func=lambda g: GAME_OPTIONS[g],
    )
    if chosen_game != st.session_state.selected_game_id:
        if prev := get_play_store(st.session_state.selected_game_id):
            prev.persist(st)
        st.session_state.selected_game_id = chosen_game
        st.session_state.messages = []
        st.session_state.last_sources = []
        sync_deck(chosen_game, _deck_char_id(chosen_game))
        st.rerun()

    selected_game_id = st.session_state.selected_game_id
    selected_game = get_game_config(selected_game_id)
    plugin = get_game_plugin(selected_game_id)
    all_factions = get_all_factions(selected_game_id)

    anthropic_key = _resolve_anthropic_key()
    chat_providers = available_chat_providers(anthropic_key=anthropic_key)
    if st.session_state.chat_provider not in chat_providers:
        st.session_state.chat_provider = "ollama"
    if len(chat_providers) > 1:
        provider_labels = {provider_display_name(p): p for p in chat_providers}
        label_options = list(provider_labels.keys())
        current_label = provider_display_name(st.session_state.chat_provider)
        chosen_label = st.selectbox(
            "Chat provider",
            options=label_options,
            index=label_options.index(current_label),
        )
        chat_provider: ChatProvider = provider_labels[chosen_label]
        st.session_state.chat_provider = chat_provider
    else:
        chat_provider = "ollama"
        st.session_state.chat_provider = chat_provider

    st.caption(f"Chat model: `{active_model_name(chat_provider)}`")
    st.caption(f"Embedding model: `{EMBED_MODEL}`")
    mode = st.radio("Mode", ["RAG", "Agent"], help="Agent routes to tools when enabled.")
    top_k = st.slider("Retrieval top-k", 3, 12, 5)
    retrieval_profile = st.selectbox(
        "Retrieval profile",
        options=list(RETRIEVAL_PROFILES.keys()),
        index=0,
        help="Quality raises internal candidate depth and uses hybrid retrieval.",
    )
    retrieval_cfg = RETRIEVAL_PROFILES[retrieval_profile]
    selected_factions = st.multiselect(
        "Source filters (RAG mode)",
        options=all_factions,
        default=all_factions,
        format_func=lambda x: FACTION_LABELS.get(x, x),
    )
    ingest_all = st.checkbox(plugin.ingest_all_label(), value=True)
    ocr_available = bool(selected_game.get("ocr_pdfs"))
    use_ocr = False
    force_ocr = False
    if ocr_available:
        use_ocr = st.checkbox(
            "OCR for image PDFs",
            value=True,
            help="Uses cached OCR in data/ocr_cache/ after the first run.",
        )
        force_ocr = st.checkbox("Force re-OCR (ignore cache)", value=False)

    if selected_game.get("has_game_state"):
        st.divider()
        wh40k_ui.render_game_sidebar()

    if selected_game.get("has_character_sheet"):
        st.divider()
        bt_ui.render_character_sidebar()

    st.divider()
    bt_char_id = _deck_char_id(selected_game_id) if selected_game.get("has_play_roster") else None
    bt_card_source = "virtual"
    if bt_char_id:
        _, bt_card_source = _play_settings(selected_game_id)
    render_deck_sidebar(
        selected_game_id,
        char_id=bt_char_id,
        card_source=bt_card_source,
    )

    if selected_game.get("has_character_sheet"):
        st.divider()
        bt_ui.render_shortcuts(
            selected_game_id,
            mode=mode,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
            chat_provider=chat_provider,
        )

    render_index_section(
        selected_game_id=selected_game_id,
        selected_game=selected_game,
        ingest_all=ingest_all,
        use_ocr=use_ocr,
        force_ocr=force_ocr,
    )

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

chat_placeholder = (
    "Ask about rules… or /roll 2d6+1, /draw 1, /deck reset"
    if plugin.has_game_state
    else bt_ui.chat_placeholder()
)

if prompt := st.chat_input(chat_placeholder):
    prior_history = recent_chat_history(MEMORY_MESSAGES)
    game_state = wh40k_ui.get_game_state() if plugin.has_game_state else None
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer, sources, route = _answer_user_prompt(
                    prompt,
                    mode=mode,
                    game_id=st.session_state.selected_game_id,
                    game_state=game_state,
                    prior_history=prior_history,
                    retrieval_cfg=retrieval_cfg,
                    top_k=top_k,
                    selected_factions=selected_factions,
                    chat_provider=st.session_state.chat_provider,
                )
            except Exception as e:
                if st.session_state.get("chat_provider") == "claude":
                    answer = (
                        f"Error: {e}\n\n"
                        "Ensure ANTHROPIC_API_KEY is set. "
                        "Ollama is still required for embeddings."
                    )
                else:
                    answer = f"Error: {e}\n\nEnsure Ollama is running and models are pulled."
                sources = []
                route = ""

        if route:
            st.caption(f"Route: {route}")

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_sources = sources

with st.sidebar:
    render_sources_sidebar()
