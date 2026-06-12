"""Shared Streamlit sidebar components."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config import CHAT_MODEL, EMBED_MODEL, GAME_BRAMBLETREK, OCR_CACHE_DIR, get_mvp_pdfs, get_pdf_sources
from src.games.saves import get_play_store
from src.ingest import run_ingest, tyranids_codex_needs_ocr
from src.rag import index_exists
from src.tools import (
    deck_remaining,
    deck_scope_key,
    draw_cards,
    format_card_result,
    format_dice_result,
    get_deck_snapshot,
    register_physical_card,
    reset_deck,
    roll_dice,
    sync_deck_store,
)

ROOT = Path(__file__).resolve().parent.parent.parent

FACTION_LABELS = {
    "core": "Core / Quickstart",
    "space_marines": "Codex: Space Marines",
    "tyranids": "Codex: Tyranids",
    "cards_sm": "SM Datasheets",
    "cards_nids": "Tyranid Datasheets",
    "supplement": "Supplement",
    "adventure": "Adventure",
}

RETRIEVAL_PROFILES = {
    "Fast": {"candidate_k": 14, "use_hybrid": False},
    "Balanced": {"candidate_k": 24, "use_hybrid": True},
    "Quality": {"candidate_k": 70, "use_hybrid": True},
}

MEMORY_MESSAGES = 10


def deck_key(game_id: str, char_id: str | None = None) -> str:
    if game_id == GAME_BRAMBLETREK and char_id:
        return f"deck_{game_id}_{char_id}"
    return f"deck_{game_id}"


def deck_scope(game_id: str, char_id: str | None = None) -> str:
    return deck_scope_key(game_id, char_id)


def sync_deck(game_id: str, char_id: str | None = None) -> None:
    scope = deck_scope(game_id, char_id)
    deck = st.session_state.get(deck_key(game_id, char_id))
    sync_deck_store(scope, deck)


def refresh_deck(game_id: str, char_id: str | None = None) -> None:
    scope = deck_scope(game_id, char_id)
    st.session_state[deck_key(game_id, char_id)] = get_deck_snapshot(scope)


def render_deck_sidebar(
    game_id: str,
    *,
    char_id: str | None = None,
    card_source: str = "virtual",
) -> None:
    st.subheader("Table deck")
    sync_deck(game_id, char_id)
    scope = deck_scope(game_id, char_id)
    remaining = deck_remaining(scope)
    st.caption(f"{remaining} cards remaining (per character)" if char_id else f"{remaining} cards remaining")

    physical = card_source == "physical" and game_id == GAME_BRAMBLETREK

    if physical:
        report = st.text_input(
            "Report physical card",
            value="",
            key=f"deck_report_{game_id}_{char_id or 'default'}",
            placeholder="Queen of Hearts or Q♥",
        )
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Record card", key=f"deck_report_btn_{game_id}_{char_id}"):
                if report.strip():
                    result = register_physical_card(report, game_id=game_id, char_id=char_id)
                    refresh_deck(game_id, char_id)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": format_card_result(result)}
                    )
                    if char_id and result.get("ok") and result.get("cards"):
                        store = get_play_store(game_id)
                        if store:
                            store.log_draw(char_id, result["cards"], label="Physical draw", st=st)
                    st.rerun()
        with col2:
            if st.button("Virtual draw (AI)", key=f"deck_virtual_{game_id}_{char_id}"):
                result = draw_cards(count=1, game_id=game_id, char_id=char_id)
                refresh_deck(game_id, char_id)
                st.session_state.messages.append(
                    {"role": "assistant", "content": format_card_result(result)}
                )
                if char_id and result.get("ok") and result.get("cards"):
                    store = get_play_store(game_id)
                    if store:
                        store.log_draw(char_id, result["cards"], st=st)
                st.rerun()
    else:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Draw 1", key=f"deck_draw_{game_id}_{char_id or ''}"):
                result = draw_cards(count=1, game_id=game_id, char_id=char_id)
                refresh_deck(game_id, char_id)
                st.session_state.messages.append(
                    {"role": "assistant", "content": format_card_result(result)}
                )
                if char_id and result.get("ok") and result.get("cards"):
                    store = get_play_store(game_id)
                    if store:
                        store.log_draw(char_id, result["cards"], st=st)
                st.rerun()
        with col2:
            if st.button("Reset deck", key=f"deck_reset_{game_id}_{char_id or ''}"):
                reset_deck(game_id=game_id, char_id=char_id)
                refresh_deck(game_id, char_id)
                st.success("Deck reshuffled.")
                st.rerun()

    roll_expr = st.text_input("Quick roll", value="d6", key=f"quick_roll_{game_id}_{char_id or ''}")
    if st.button("Roll", key=f"deck_roll_{game_id}_{char_id or ''}"):
        result = roll_dice(roll_expr)
        st.session_state.messages.append(
            {"role": "assistant", "content": format_dice_result(result)}
        )
        if char_id and result.get("ok"):
            store = get_play_store(game_id)
            if store:
                store.log_roll(char_id, "", result=result, st=st)
        st.rerun()


def render_index_section(
    *,
    selected_game_id: str,
    selected_game: dict,
    ingest_all: bool,
    use_ocr: bool,
    force_ocr: bool,
) -> None:
    st.divider()
    st.subheader("Index")
    indexed = index_exists(game_id=selected_game_id)
    st.write("Status:", "Ready" if indexed else "Not indexed")
    if (
        selected_game_id == "40k"
        and ingest_all
        and use_ocr
        and tyranids_codex_needs_ocr()
        and not (OCR_CACHE_DIR / "Codex - Tyranids (10th Edition).json").exists()
    ):
        st.warning("Tyranids codex needs OCR first run (10–30 min).")

    if st.button("Reindex documents", type="primary"):
        msg = "Indexing PDFs..."
        if use_ocr and ingest_all:
            msg = "Indexing (OCR for image PDFs if needed — first run can take 10–30 min)..."
        with st.spinner(msg):
            code = run_ingest(
                game_id=selected_game_id,
                mvp_only=not ingest_all,
                reset=True,
                use_ocr=use_ocr,
                force_ocr=force_ocr,
            )
        if code == 0:
            st.success("Index updated.")
        else:
            st.error("Indexing failed. Check docs/, Ollama, and Tesseract (brew install tesseract).")

    st.divider()
    st.subheader("Docs expected")
    pdf_sources = get_pdf_sources(selected_game_id)
    mvp_pdfs = get_mvp_pdfs(selected_game_id)
    for name, meta in pdf_sources.items():
        path = ROOT / "docs" / name
        mark = "✓" if path.exists() else "○"
        mvp = " (MVP)" if name in mvp_pdfs else ""
        st.text(f"{mark} {meta['label']}{mvp}")


def render_sources_sidebar() -> None:
    st.divider()
    st.subheader("Sources (last reply)")
    sources = st.session_state.get("last_sources", [])
    if not sources:
        st.caption("No sources yet.")
    for i, src in enumerate(sources, 1):
        label = src.get("source_label") or src.get("source_file", "?")
        page = src.get("page", "?")
        score = src.get("score")
        title = f"{i}. {label} — p.{page}"
        if score is not None:
            title += f" (score {score})"
        with st.expander(title):
            st.caption(f"Faction: {src.get('faction', '')}")
            st.text(src.get("text", "")[:2000])


def recent_chat_history(max_messages: int = MEMORY_MESSAGES) -> list[dict[str, str]]:
    msgs = st.session_state.get("messages", [])
    return [m for m in msgs[-max_messages:] if m.get("role") in {"user", "assistant"}]


def to_langchain_history(history: list[dict[str, str]]):
    from langchain_core.messages import AIMessage, HumanMessage

    out = []
    for msg in history:
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        if msg.get("role") == "user":
            out.append(HumanMessage(content=content))
        elif msg.get("role") == "assistant":
            out.append(AIMessage(content=content))
    return out
