"""Streamlit UI for rulebook-ai."""

from __future__ import annotations

import html
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from src.agent import run_agent
from src.brambletrek_character import (
    character_from_dict,
    character_to_dict,
    default_character,
    format_summary as format_character_summary,
    get_legacy_options,
    label_for_band,
    load_saved_character,
    save_character,
    table_options,
)
from src.brambletrek_curated import (
    adventure_options,
    apply_single_journey_event,
    format_reason_ending,
    journey_depths_trace,
    legacy_abilities,
    lookup_journey_event,
    overcome_the_odds,
    reset_daily_legacy_abilities,
)
from src.brambletrek_actions import (
    match_brambletrek_shortcut,
    run_shortcut,
    shortcuts_for_character,
)
from src.config import (
    CHAT_MODEL,
    DEFAULT_GAME_ID,
    EMBED_MODEL,
    GAME_40K,
    GAME_BRAMBLETREK,
    GAME_CATALOG,
    OCR_CACHE_DIR,
    get_all_factions,
    get_game_config,
    get_mvp_pdfs,
    get_pdf_sources,
)
from src.game_state import (
    default_state,
    format_summary,
    game_state_from_dict,
    game_state_to_dict,
)
from src.ingest import run_ingest, tyranids_codex_needs_ocr
from src.rag import index_exists, query as rag_query
from src.tools import (
    deck_remaining,
    draw_cards,
    extract_dice_expression,
    format_card_result,
    format_dice_result,
    get_deck_snapshot,
    is_card_plus_rules_question,
    is_card_question,
    is_dice_question,
    reset_deck,
    roll_dice,
    run_explicit_command,
    sync_deck_store,
)

FACTION_LABELS = {
    "core": "Core / Quickstart",
    "space_marines": "Codex: Space Marines",
    "tyranids": "Codex: Tyranids",
    "cards_sm": "SM Datasheets",
    "cards_nids": "Tyranid Datasheets",
    "supplement": "Supplement",
    "adventure": "Adventure",
}

GAME_OPTIONS = {
    GAME_40K: GAME_CATALOG[GAME_40K]["label"],
    GAME_BRAMBLETREK: GAME_CATALOG[GAME_BRAMBLETREK]["label"],
}

ARMY_OPTIONS = {
    "": "—",
    "space_marines": "Space Marines",
    "tyranids": "Tyranids",
}

PHASE_OPTIONS = {
    "": "—",
    "command": "Command",
    "movement": "Movement",
    "shooting": "Shooting",
    "charge": "Charge",
    "fight": "Fight",
}

ACTIVE_OPTIONS = {
    "": "—",
    "me": "Me",
    "opponent": "Opponent",
}

RETRIEVAL_PROFILES = {
    "Fast": {"candidate_k": 14, "use_hybrid": False},
    "Balanced": {"candidate_k": 24, "use_hybrid": True},
    "Quality": {"candidate_k": 70, "use_hybrid": True},
}
MEMORY_MESSAGES = 10


def _deck_key(game_id: str) -> str:
    return f"deck_{game_id}"


def _init_session() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "last_sources" not in st.session_state:
        st.session_state.last_sources = []
    if "game" not in st.session_state:
        st.session_state.game = game_state_to_dict(default_state())
    if "selected_game_id" not in st.session_state:
        st.session_state.selected_game_id = DEFAULT_GAME_ID
    for gid in GAME_OPTIONS:
        key = _deck_key(gid)
        if key not in st.session_state:
            st.session_state[key] = None
    if "bt_character" not in st.session_state:
        saved = load_saved_character()
        st.session_state.bt_character = character_to_dict(saved or default_character())
def _get_bt_character():
    return character_from_dict(st.session_state.get("bt_character"))


def _brambletrek_shortcut_kwargs() -> dict:
    char = _get_bt_character()
    return {
        "in_aldwund": char.in_aldwund,
        "reason_band": char.reason_band,
        "active_adventure": char.active_adventure,
    }


def _persist_bt_character(data: dict) -> None:
    char = character_from_dict(data)
    char.clamp_stats()
    st.session_state.bt_character = character_to_dict(char)
    save_character(char)


def _journey_event_stat_preview(event: dict) -> str:
    parts: list[str] = []
    for key, icon in (("health", "Health"), ("morale", "Morale"), ("supplies", "Supplies")):
        val = event.get(key)
        if val is not None and val != 0:
            sign = "+" if int(val) > 0 else ""
            parts.append(f"{icon} {sign}{val}")
    if event.get("all_stats") is not None:
        v = int(event["all_stats"])
        sign = "+" if v > 0 else ""
        parts.append(f"All stats {sign}{v}")
    if event.get("combat"):
        parts.append("Combat")
    for tag in event.get("tags") or []:
        parts.append(f"({tag.upper()})")
    return ", ".join(parts) if parts else "—"


def _stash_pending_journey(run: dict, shortcut_id: str) -> str:
    """Queue journey cards for per-event sheet updates in the sidebar."""
    cards = run.get("journey_cards")
    if not cards or shortcut_id not in ("journey_day", "aldwund_day"):
        return ""
    char = _get_bt_character()
    st.session_state.bt_pending_journey = {
        "cards": cards,
        "applied": [False] * len(cards),
        "depths_trace": journey_depths_trace(cards, start_in_aldwund=char.in_aldwund),
        "shortcut_id": shortcut_id,
    }
    return (
        "\n\n_Apply each event in the sidebar **Today's draws** when you resolve it "
        "(combat, abilities, and items happen between cards — not all at once)._"
    )


def _render_pending_journey_panel(c: dict) -> None:
    pending = st.session_state.get("bt_pending_journey")
    if not pending:
        return

    cards = pending.get("cards") or []
    applied = list(pending.get("applied") or [False] * len(cards))
    trace = pending.get("depths_trace") or journey_depths_trace(
        cards, start_in_aldwund=bool(c.get("in_aldwund"))
    )

    st.markdown("**Today's draws** (core journey)")
    st.caption(
        "Hyhill Journey & Exploration curated tables (pp. 24–27). "
        "Adventure modules use **Adventure scene** + PDF lookup instead."
    )
    st.caption(
        "Resolve events in order. Apply stats when each card is done — "
        "pause for combat or Legacy abilities between cards."
    )

    char = _get_bt_character()
    for i, card in enumerate(cards):
        in_depths = trace[i] if i < len(trace) else char.in_aldwund
        event = lookup_journey_event(card, in_depths=in_depths)
        label = event.get("label", card) if event else card
        zone = "depths" if in_depths else "surface"
        done = applied[i] if i < len(applied) else False

        with st.container(border=True):
            status = "✓ Applied" if done else "Pending"
            st.markdown(f"**Event {i + 1}** — `{card}` · _{zone}_ · {status}")
            if event:
                extra = _journey_event_stat_preview(event)
                if extra != "—":
                    st.caption(extra)
            prev_done = i == 0 or (i > 0 and applied[i - 1])
            if done:
                st.caption(label)
            elif st.button(
                "Apply to sheet",
                key=f"bt_apply_event_{i}",
                disabled=not prev_done,
                use_container_width=True,
            ):
                summary = apply_single_journey_event(char, card, in_depths=in_depths)
                applied[i] = True
                pending["applied"] = applied
                st.session_state.bt_pending_journey = pending
                _persist_bt_character(character_to_dict(char))
                st.toast(summary.replace("**", ""), icon="✅")
                st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Finish day", key="bt_finish_journey_day", use_container_width=True):
            char.journey_day = max(1, char.journey_day + 1)
            reset_daily_legacy_abilities(char)
            char.clamp_stats()
            _persist_bt_character(character_to_dict(char))
            del st.session_state.bt_pending_journey
            st.rerun()
    with col_b:
        if st.button("Discard draws", key="bt_clear_pending", use_container_width=True):
            del st.session_state.bt_pending_journey
            st.rerun()

    with st.expander("Quick bulk apply (optional)"):
        st.caption(
            "Applies all remaining non-combat stats at once and does not advance the day. "
            "Inaccurate if you stopped for combat mid-day."
        )
        if st.button("Bulk apply non-combat stats", key="bt_bulk_apply"):
            for i, card in enumerate(cards):
                if applied[i]:
                    continue
                ev = lookup_journey_event(
                    card, in_depths=trace[i] if i < len(trace) else char.in_aldwund
                )
                if ev and ev.get("combat"):
                    continue
                apply_single_journey_event(
                    char, card, in_depths=trace[i] if i < len(trace) else char.in_aldwund
                )
                applied[i] = True
            pending["applied"] = applied
            st.session_state.bt_pending_journey = pending
            _persist_bt_character(character_to_dict(char))
            st.rerun()


def _sync_deck(game_id: str) -> None:
    deck = st.session_state.get(_deck_key(game_id))
    sync_deck_store(game_id, deck)


def _refresh_deck(game_id: str) -> None:
    st.session_state[_deck_key(game_id)] = get_deck_snapshot(game_id)


def _select_index(options: list[tuple[str, str]], current: str) -> int:
    ids = [o[0] for o in options]
    if current in ids:
        return ids.index(current)
    return 0


_LEGACY_STYLES_INJECTED = False

_LEGACY_STYLES = """
<style>
.bt-legacy-wrap { margin: 0.35rem 0 0.75rem 0; }
.bt-legacy-title {
    font-size: 0.82rem; font-weight: 600; letter-spacing: 0.04em;
    text-transform: uppercase; color: rgba(250, 250, 250, 0.55);
    margin: 0 0 0.5rem 0;
}
.bt-ability-row {
    display: flex; flex-wrap: wrap; align-items: center; gap: 0.35rem 0.5rem;
    margin-bottom: 0.25rem;
}
.bt-ability-name { font-size: 0.95rem; font-weight: 600; color: #f3f4f6; line-height: 1.3; }
.bt-ability-name.used { color: #9ca3af; text-decoration: line-through; text-decoration-color: rgba(156,163,175,0.5); }
.bt-badge {
    display: inline-block; padding: 0.12rem 0.45rem; border-radius: 999px;
    font-size: 0.68rem; font-weight: 600; letter-spacing: 0.02em; line-height: 1.4;
}
.bt-badge-ready {
    background: rgba(16, 185, 129, 0.18); color: #6ee7b7;
    border: 1px solid rgba(110, 231, 183, 0.35);
}
.bt-badge-used {
    background: rgba(107, 114, 128, 0.2); color: #d1d5db;
    border: 1px solid rgba(156, 163, 175, 0.35);
}
.bt-tag {
    display: inline-block; padding: 0.1rem 0.4rem; border-radius: 4px;
    font-size: 0.65rem; font-weight: 500; text-transform: capitalize;
}
.bt-tag-combat { background: rgba(239, 68, 68, 0.15); color: #fca5a5; }
.bt-tag-exploration { background: rgba(59, 130, 246, 0.15); color: #93c5fd; }
.bt-tag-universal { background: rgba(217, 119, 6, 0.15); color: #fcd34d; }
.bt-ability-body { padding-bottom: 0.85rem; }
.bt-ability-desc {
    font-size: 0.8rem; color: rgba(209, 213, 219, 0.85); line-height: 1.45;
    margin: 0.2rem 0 0 0; padding-bottom: 0.15rem;
}
.bt-oto-label {
    font-size: 0.72rem; color: rgba(250, 204, 21, 0.75); font-weight: 500;
    display: block; margin: 0.15rem 0 0.2rem 0;
}
.bt-legacy-boost { font-size: 0.8rem; margin: -0.25rem 0 0.5rem 0; }
.bt-boost-up { color: #6ee7b7; font-weight: 500; }
.bt-boost-down { color: #fca5a5; font-weight: 500; }
.bt-boost-sep { color: rgba(156, 163, 175, 0.6); }
</style>
"""


def _inject_legacy_ability_styles() -> None:
    global _LEGACY_STYLES_INJECTED
    if not _LEGACY_STYLES_INJECTED:
        st.markdown(_LEGACY_STYLES, unsafe_allow_html=True)
        _LEGACY_STYLES_INJECTED = True


def _legacy_tag_html(tags: list[str] | None) -> str:
    if not tags:
        return ""
    parts = []
    for tag in tags:
        cls = f"bt-tag bt-tag-{tag}" if tag in ("combat", "exploration", "universal") else "bt-tag"
        parts.append(f'<span class="{cls}">{tag}</span>')
    return " ".join(parts)


def _legacy_ability_header_html(label: str, used: bool, tags: list[str] | None = None) -> str:
    safe_label = html.escape(label)
    name_cls = "bt-ability-name used" if used else "bt-ability-name"
    badge_cls = "bt-badge bt-badge-used" if used else "bt-badge bt-badge-ready"
    badge_text = "Used today" if used else "Ready"
    tag_html = _legacy_tag_html(tags)
    return (
        f'<div class="bt-ability-row">'
        f'<span class="{name_cls}">{safe_label}</span>'
        f'<span class="{badge_cls}">{badge_text}</span>'
        f"{tag_html}"
        f"</div>"
    )


def _render_legacy_abilities_panel(
    legacy_id: str,
    used_map: dict[str, bool],
) -> dict[str, bool]:
    """Render daily abilities with cards; return updated used_map."""
    _inject_legacy_ability_styles()
    st.markdown('<p class="bt-legacy-title">Daily abilities</p>', unsafe_allow_html=True)

    for ab in legacy_abilities(legacy_id):
        ab_id = ab["id"]
        is_used = used_map.get(ab_id, False)
        with st.container(border=True):
            head_l, head_r = st.columns([0.14, 0.86], vertical_alignment="center")
            with head_l:
                used_map[ab_id] = st.checkbox(
                    "Used",
                    value=is_used,
                    key=f"bt_ab_{legacy_id}_{ab_id}",
                    label_visibility="collapsed",
                    help="Mark as used today",
                )
            with head_r:
                desc = html.escape(str(ab.get("description", "")))
                st.markdown(
                    f'<div class="bt-ability-body">'
                    f"{_legacy_ability_header_html(ab['label'], used_map[ab_id], ab.get('tags'))}"
                    f'<p class="bt-ability-desc">{desc}</p></div>',
                    unsafe_allow_html=True,
                )

    oto = overcome_the_odds()
    oto_id = oto["id"]
    with st.container(border=True):
        head_l, head_r = st.columns([0.14, 0.86], vertical_alignment="center")
        with head_l:
            used_map[oto_id] = st.checkbox(
                "Used",
                value=used_map.get(oto_id, False),
                key=f"bt_ab_{legacy_id}_{oto_id}",
                label_visibility="collapsed",
                help="Mark Overcome the Odds as used today",
            )
        with head_r:
            oto_desc = html.escape(str(oto.get("description", "")))
            st.markdown(
                f'<div class="bt-ability-body">'
                f"{_legacy_ability_header_html(oto['label'], used_map[oto_id], ['universal'])}"
                f'<span class="bt-oto-label">Shared by all Legacies</span>'
                f'<p class="bt-ability-desc">{oto_desc}</p></div>',
                unsafe_allow_html=True,
            )

    return used_map


def _render_brambletrek_character_sidebar() -> None:
    st.subheader("Your Gnawborn")
    c = dict(st.session_state.bt_character)

    c["name"] = st.text_input("Name", value=c.get("name", ""), key="bt_name")

    reason_opts = table_options("reasons")
    c["reason_band"] = st.selectbox(
        "Reason for adventure",
        options=[o[0] for o in reason_opts],
        index=_select_index(reason_opts, c.get("reason_band", "")),
        format_func=lambda k: next(label for i, label in reason_opts if i == k),
        key="bt_reason_band",
    )
    c["reason_card"] = st.text_input(
        "Reason card (optional)",
        value=c.get("reason_card", ""),
        placeholder="e.g. 8 of diamonds",
        key="bt_reason_card",
    )

    bg_opts = table_options("backgrounds")
    c["background_band"] = st.selectbox(
        "Background",
        options=[o[0] for o in bg_opts],
        index=_select_index(bg_opts, c.get("background_band", "")),
        format_func=lambda k: next(label for i, label in bg_opts if i == k),
        key="bt_background_band",
    )
    c["background_card"] = st.text_input(
        "Background card (optional)",
        value=c.get("background_card", ""),
        key="bt_background_card",
    )

    trinket_opts = table_options("trinkets")
    c["trinket_band"] = st.selectbox(
        "Trinket",
        options=[o[0] for o in trinket_opts],
        index=_select_index(trinket_opts, c.get("trinket_band", "")),
        format_func=lambda k: next(label for i, label in trinket_opts if i == k),
        key="bt_trinket_band",
    )
    c["trinket_card"] = st.text_input(
        "Trinket card (optional)",
        value=c.get("trinket_card", ""),
        key="bt_trinket_card",
    )

    legacy_opts = get_legacy_options()
    legacy_ids = list(legacy_opts.keys())
    c["legacy"] = st.selectbox(
        "Legacy",
        options=legacy_ids,
        index=_select_index([(i, legacy_opts[i]["label"]) for i in legacy_ids], c.get("legacy", "")),
        format_func=lambda k: legacy_opts[k]["label"],
        key="bt_legacy",
    )
    leg = legacy_opts.get(c["legacy"], {})
    if leg.get("boost"):
        st.markdown(
            f'<p class="bt-legacy-boost">'
            f'<span class="bt-boost-up">{html.escape(leg["boost"])}</span>'
            f' <span class="bt-boost-sep">·</span> '
            f'<span class="bt-boost-down">{html.escape(leg["flaw"])}</span>'
            f"</p>",
            unsafe_allow_html=True,
        )

    if c.get("legacy"):
        _inject_legacy_ability_styles()
        prev_legacy = st.session_state.get("bt_last_legacy")
        used_map: dict[str, bool] = dict(c.get("legacy_abilities_used") or {})
        if prev_legacy is not None and prev_legacy != c["legacy"]:
            used_map = {}
        st.session_state.bt_last_legacy = c["legacy"]

        used_map = _render_legacy_abilities_panel(c["legacy"], used_map)

        c["legacy_abilities_used"] = used_map
        if st.button(
            "Reset daily abilities",
            key="bt_reset_abilities",
            type="secondary",
            use_container_width=True,
        ):
            c["legacy_abilities_used"] = {}
            st.rerun()

    _render_pending_journey_panel(c)

    st.markdown("**Resources** (max 20 each)")
    r1, r2, r3 = st.columns(3)
    with r1:
        c["health"] = st.number_input("Health", min_value=0, max_value=20, value=int(c.get("health", 10)), key="bt_health")
    with r2:
        c["morale"] = st.number_input("Morale", min_value=0, max_value=20, value=int(c.get("morale", 10)), key="bt_morale")
    with r3:
        c["supplies"] = st.number_input("Supplies", min_value=0, max_value=20, value=int(c.get("supplies", 10)), key="bt_supplies")

    c["journey_day"] = st.number_input(
        "Journey day",
        min_value=1,
        max_value=999,
        value=int(c.get("journey_day", 1)),
        key="bt_journey_day",
    )
    c["in_aldwund"] = st.checkbox(
        "In Aldwund (Depths)",
        value=bool(c.get("in_aldwund", False)),
        key="bt_in_aldwund",
        help="Journey day uses depths tables (pp. 26–27). Set automatically on (DEPTHS), cleared on (EXIT).",
    )

    adv_opts = adventure_options()
    c["active_adventure"] = st.selectbox(
        "Active adventure",
        options=[o[0] for o in adv_opts],
        index=_select_index(adv_opts, c.get("active_adventure", "")),
        format_func=lambda k: next(label for i, label in adv_opts if i == k),
        key="bt_active_adventure",
        help="Adventure scenes come from this module's PDF (RAG). Core journey curated tables apply for Hyhill solo or Journey/Aldwund shortcuts.",
    )

    if c.get("reason_band"):
        with st.expander("Reason ending preview (p. 36)"):
            st.markdown(
                format_reason_ending(
                    c["reason_band"],
                    reason_label=label_for_band("reasons", c["reason_band"]),
                )
            )

    c["notes"] = st.text_area("Journal notes", value=c.get("notes", ""), height=80, key="bt_notes")

    _persist_bt_character(c)

    if st.button("Reset character", key="bt_reset"):
        st.session_state.bt_character = character_to_dict(default_character())
        save_character(default_character())
        st.rerun()


def _answer_table_lookup_prompt(
    prompt: str,
    *,
    game_id: str,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
) -> tuple[str, list[dict], str]:
    """RAG lookup after local deck pulls (avoids a second draw from card_rag)."""
    factions = selected_factions if selected_factions else None
    effective_top_k = max(top_k, 8)
    lower = prompt.lower()
    if "random gnawborn" in lower or "character creation" in lower:
        effective_top_k = max(effective_top_k, 12)
    if "adventure scene" in lower:
        effective_top_k = max(effective_top_k, 14)
    if "journey" in lower or "exploration" in lower or "event 1" in lower:
        effective_top_k = max(effective_top_k, 12)
    result = rag_query(
        prompt,
        top_k=effective_top_k,
        factions=factions,
        game_state=None,
        game_id=game_id,
        chat_history=[],
        candidate_k=retrieval_cfg["candidate_k"],
        use_hybrid=retrieval_cfg["use_hybrid"],
        brambletrek_character=_get_bt_character() if game_id == GAME_BRAMBLETREK else None,
    )
    return result.answer, result.sources, "rag"


def _execute_brambletrek_shortcut_answer(
    shortcut_id: str,
    *,
    mode: str,
    game_id: str,
    game_state,
    prior_history: list[dict[str, str]],
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
) -> tuple[str, list[dict], str]:
    """Run a matched shortcut and return (answer, sources, route)."""
    run = run_shortcut(shortcut_id, game_id=game_id, **_brambletrek_shortcut_kwargs())
    kind = run["kind"]
    route = f"brambletrek:{shortcut_id}"

    if kind in {"multi_draw_rag", "rag_only", "roll_rag"}:
        answer, sources, _ = _answer_table_lookup_prompt(
            run["prompt"],
            game_id=game_id,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
        )
        if kind in {"multi_draw_rag", "roll_rag"}:
            stat_note = _stash_pending_journey(run, shortcut_id)
            answer = f"{run['user_message']}{stat_note}\n\n{answer}"
        _refresh_deck(game_id)
        return answer, sources, route

    out = run_agent(
        run["prompt"],
        history=_to_langchain_history(prior_history),
        game_state=game_state,
        game_id=game_id,
        retrieval=retrieval_cfg,
        brambletrek_character=st.session_state.get("bt_character"),
    )
    _refresh_deck(game_id)
    return out["answer"], out.get("sources", []), route


def _run_brambletrek_shortcut(
    shortcut_id: str,
    *,
    mode: str,
    game_id: str,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
) -> None:
    _sync_deck(game_id)
    run = run_shortcut(shortcut_id, game_id=game_id, **_brambletrek_shortcut_kwargs())
    prior_history = _recent_chat_history()
    st.session_state.messages.append({"role": "user", "content": run["user_message"]})

    kind = run["kind"]
    if kind in {"multi_draw_rag", "rag_only", "roll_rag"}:
        answer, sources, _route = _answer_table_lookup_prompt(
            run["prompt"],
            game_id=game_id,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
        )
        if kind in {"multi_draw_rag", "roll_rag"}:
            stat_note = _stash_pending_journey(run, shortcut_id)
            answer = f"{run['user_message']}{stat_note}\n\n{answer}"
    else:
        answer, sources, _route = _answer_user_prompt(
            run["prompt"],
            mode=mode,
            game_id=game_id,
            game_state=None,
            prior_history=prior_history,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
        )

    _refresh_deck(game_id)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_sources = sources
    st.rerun()


def _render_brambletrek_shortcuts(
    game_id: str,
    *,
    mode: str,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
) -> None:
    st.subheader("Brambletrek shortcuts")
    char = _get_bt_character()
    active_adv = char.active_adventure or ""
    st.caption(
        "Core Hyhill journey uses curated tables (pp. 24–27). "
        "With an active adventure, use **Adventure scene** — scenes from the PDF via RAG."
    )

    for shortcut in shortcuts_for_character(active_adventure=active_adv):
        sid = shortcut["id"]
        if st.button(shortcut["label"], key=f"bt_shortcut_{sid}"):
            _run_brambletrek_shortcut(
                sid,
                mode=mode,
                game_id=game_id,
                retrieval_cfg=retrieval_cfg,
                top_k=top_k,
                selected_factions=selected_factions,
            )


def _render_deck_sidebar(game_id: str) -> None:
    st.subheader("Table deck")
    _sync_deck(game_id)
    remaining = deck_remaining(game_id)
    st.caption(f"{remaining} cards remaining (per game session)")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Draw 1", key=f"deck_draw_{game_id}"):
            result = draw_cards(count=1, game_id=game_id)
            _refresh_deck(game_id)
            st.session_state.messages.append(
                {"role": "assistant", "content": format_card_result(result)}
            )
            st.rerun()
    with col2:
        if st.button("Reset deck", key=f"deck_reset_{game_id}"):
            reset_deck(game_id=game_id)
            _refresh_deck(game_id)
            st.success("Deck reshuffled.")
            st.rerun()

    roll_expr = st.text_input("Quick roll", value="d6", key=f"quick_roll_{game_id}")
    if st.button("Roll", key=f"deck_roll_{game_id}"):
        result = roll_dice(roll_expr)
        st.session_state.messages.append(
            {"role": "assistant", "content": format_dice_result(result)}
        )
        st.rerun()


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
) -> tuple[str, list[dict], str]:
    """Return (answer, sources, route_label)."""
    _sync_deck(game_id)

    cmd = run_explicit_command(prompt, game_id=game_id)
    if cmd is not None:
        _refresh_deck(game_id)
        return cmd.get("answer", ""), cmd.get("sources", []), cmd.get("route", "command")

    if game_id == GAME_BRAMBLETREK:
        stripped = prompt.strip().lower()
        if stripped in {"/day", "/journey"}:
            day_shortcut = (
                "adventure_scene"
                if (_get_bt_character().active_adventure or "")
                else "journey_day"
            )
            return _execute_brambletrek_shortcut_answer(
                day_shortcut,
                mode=mode,
                game_id=game_id,
                game_state=game_state,
                prior_history=prior_history,
                retrieval_cfg=retrieval_cfg,
                top_k=top_k,
                selected_factions=selected_factions,
            )
        shortcut_id = match_brambletrek_shortcut(
            prompt,
            active_adventure=_get_bt_character().active_adventure or "",
        )
        if shortcut_id:
            return _execute_brambletrek_shortcut_answer(
                shortcut_id,
                mode=mode,
                game_id=game_id,
                game_state=game_state,
                prior_history=prior_history,
                retrieval_cfg=retrieval_cfg,
                top_k=top_k,
                selected_factions=selected_factions,
            )

    if mode == "Agent":
        out = run_agent(
            prompt,
            history=_to_langchain_history(prior_history),
            game_state=game_state,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=st.session_state.get("bt_character"),
        )
        _refresh_deck(game_id)
        return out["answer"], out.get("sources", []), out.get("route", "")

    if is_card_plus_rules_question(prompt):
        out = run_agent(
            prompt,
            history=_to_langchain_history(prior_history),
            game_state=game_state,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=st.session_state.get("bt_character"),
        )
        _refresh_deck(game_id)
        return out["answer"], out.get("sources", []), out.get("route", "card_rag")

    if is_dice_question(prompt):
        expr = extract_dice_expression(prompt) or "d6"
        result = roll_dice(expr)
        return format_dice_result(result), [], "dice"

    if is_card_question(prompt):
        result = draw_cards(count=1, game_id=game_id)
        _refresh_deck(game_id)
        return format_card_result(result), [], "cards"

    factions = selected_factions if selected_factions else None
    result = rag_query(
        prompt,
        top_k=top_k,
        factions=factions,
        game_state=game_state,
        game_id=game_id,
        chat_history=prior_history,
        candidate_k=retrieval_cfg["candidate_k"],
        use_hybrid=retrieval_cfg["use_hybrid"],
        brambletrek_character=_get_bt_character() if game_id == GAME_BRAMBLETREK else None,
    )
    return result.answer, result.sources, "rag"


def _get_game_state():
    return game_state_from_dict(st.session_state.game)


def _render_game_sidebar() -> None:
    st.subheader("Game State")
    g = st.session_state.game
    g["my_army"] = st.selectbox(
        "Your Army",
        options=list(ARMY_OPTIONS.keys()),
        format_func=lambda k: ARMY_OPTIONS[k],
        index=list(ARMY_OPTIONS.keys()).index(g.get("my_army", "") or ""),
        key="game_my_army",
    )
    g["opponent_army"] = st.selectbox(
        "Opponent Army",
        options=list(ARMY_OPTIONS.keys()),
        format_func=lambda k: ARMY_OPTIONS[k],
        index=list(ARMY_OPTIONS.keys()).index(g.get("opponent_army", "") or ""),
        key="game_opponent",
    )
    g["battle_round"] = st.number_input(
        "Battle Round",
        min_value=1,
        max_value=5,
        value=int(g.get("battle_round", 1)),
        key="game_round",
    )
    g["phase"] = st.selectbox(
        "Phase",
        options=list(PHASE_OPTIONS.keys()),
        format_func=lambda k: PHASE_OPTIONS[k],
        index=list(PHASE_OPTIONS.keys()).index(g.get("phase", "") or ""),
        key="game_phase",
    )
    g["active_player"] = st.selectbox(
        "Active Player",
        options=list(ACTIVE_OPTIONS.keys()),
        format_func=lambda k: ACTIVE_OPTIONS[k],
        index=list(ACTIVE_OPTIONS.keys()).index(g.get("active_player", "") or ""),
        key="game_active",
    )
    g["notes"] = st.text_area(
        "Notes",
        value=g.get("notes", ""),
        height=80,
        key="game_notes",
    )
    if st.button("Reset Game State"):
        st.session_state.game = game_state_to_dict(default_state())
        st.rerun()
    st.session_state.game = g


def _recent_chat_history(max_messages: int = MEMORY_MESSAGES) -> list[dict[str, str]]:
    msgs = st.session_state.get("messages", [])
    return [m for m in msgs[-max_messages:] if m.get("role") in {"user", "assistant"}]


def _to_langchain_history(history: list[dict[str, str]]) -> list[BaseMessage]:
    out: list[BaseMessage] = []
    for msg in history:
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        if msg.get("role") == "user":
            out.append(HumanMessage(content=content))
        elif msg.get("role") == "assistant":
            out.append(AIMessage(content=content))
    return out


st.set_page_config(
    page_title="rulebook-ai",
    page_icon="⚔️",
    layout="wide",
)

_init_session()

selected_game_id = st.session_state.selected_game_id
selected_game = get_game_config(selected_game_id)

st.title(f"{selected_game['label']} – rulebook-ai")
if selected_game_id == GAME_40K:
    st.caption(
        "Personal study helper. Always verify with official rules and your judge. "
        "GW material stays local — do not share indexes."
    )
    game_state = _get_game_state()
    summary = format_summary(game_state, "en")
    if summary:
        st.info(summary)
else:
    st.caption(
        "Personal study helper. You run the story and dice; the assistant helps "
        "interpret rule text and what roll results mean."
    )
    game_state = None
    bt_char = _get_bt_character()
    char_summary = format_character_summary(bt_char)
    if char_summary:
        st.info(char_summary)
    stat_cols = st.columns(4)
    stat_cols[0].metric("Health", bt_char.health)
    stat_cols[1].metric("Morale", bt_char.morale)
    stat_cols[2].metric("Supplies", bt_char.supplies)
    stat_cols[3].metric("Journey day", bt_char.journey_day)

with st.sidebar:
    st.header("Settings")
    chosen_game = st.selectbox(
        "Game",
        options=list(GAME_OPTIONS.keys()),
        index=list(GAME_OPTIONS.keys()).index(st.session_state.selected_game_id),
        format_func=lambda g: GAME_OPTIONS[g],
    )
    if chosen_game != st.session_state.selected_game_id:
        st.session_state.selected_game_id = chosen_game
        st.session_state.messages = []
        st.session_state.last_sources = []
        _sync_deck(chosen_game)
        st.rerun()

    selected_game_id = st.session_state.selected_game_id
    selected_game = get_game_config(selected_game_id)
    all_factions = get_all_factions(selected_game_id)
    pdf_sources = get_pdf_sources(selected_game_id)
    mvp_pdfs = get_mvp_pdfs(selected_game_id)

    st.caption(f"Chat model: `{CHAT_MODEL}`")
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
    ingest_all_label = (
        "Full ingest (include codexes)"
        if selected_game_id == GAME_40K
        else "Full ingest (include separate adventure PDFs)"
    )
    ingest_all = st.checkbox(ingest_all_label, value=True)
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
        _render_game_sidebar()

    if selected_game.get("has_character_sheet"):
        st.divider()
        _render_brambletrek_character_sidebar()

    st.divider()
    _render_deck_sidebar(selected_game_id)

    if selected_game_id == GAME_BRAMBLETREK:
        st.divider()
        _render_brambletrek_shortcuts(
            selected_game_id,
            mode=mode,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
        )

    st.divider()
    st.subheader("Index")
    indexed = index_exists(game_id=selected_game_id)
    st.write("Status:", "Ready" if indexed else "Not indexed")
    if (
        selected_game_id == GAME_40K
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
    for name, meta in pdf_sources.items():
        path = ROOT / "docs" / name
        mark = "✓" if path.exists() else "○"
        mvp = " (MVP)" if name in mvp_pdfs else ""
        st.text(f"{mark} {meta['label']}{mvp}")


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

chat_placeholder = (
    "Ask about rules… or /roll 2d6+1, /draw 1, /deck reset"
    if st.session_state.selected_game_id == GAME_40K
    else "Journey (4 cards), rules… or /day, /roll d20, /deck reset"
)


if prompt := st.chat_input(chat_placeholder):
    prior_history = _recent_chat_history()
    game_state = _get_game_state() if st.session_state.selected_game_id == GAME_40K else None
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
                )
            except Exception as e:
                answer = f"Error: {e}\n\nEnsure Ollama is running and models are pulled."
                sources = []
                route = ""

        if route:
            st.caption(f"Route: {route}")

        st.markdown(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.session_state.last_sources = sources

with st.sidebar:
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
