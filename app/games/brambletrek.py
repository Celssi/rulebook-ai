"""Brambletrek Streamlit UI and prompt handling."""

from __future__ import annotations

import html

import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from app.components.shared import recent_chat_history, refresh_deck, sync_deck, to_langchain_history
from src.agent import run_agent
from src.config import GAME_BRAMBLETREK
from src.games.brambletrek.actions import match_brambletrek_shortcut, run_shortcut, shortcuts_for_character
from src.games.brambletrek.character import (
    character_from_dict,
    character_to_dict,
    default_character,
    format_summary as format_character_summary,
    get_legacy_options,
    label_for_band,
    save_character,
    table_options,
)
from src.games.brambletrek.lonelog import (
    card_short_label,
    format_mechanical,
    format_resources,
    log_draw,
    log_mechanical,
    log_narrative,
    log_player_action,
    log_path,
    open_scene,
    read_tail,
)
from src.games.brambletrek.narrator import synthesize_narrator_line
from src.games.brambletrek.roster import create_character, delete_character, list_characters
from src.games.brambletrek.session import (
    active_char_id,
    character_session_key,
    get_play_settings,
    init_brambletrek_session,
    pending_journey_key,
    persist_current_session,
    switch_character,
)
from src.games.saves import play_setting_key
from src.games.brambletrek.curated import (
    adventure_options,
    apply_single_journey_event,
    format_reason_ending,
    journey_depths_trace,
    legacy_abilities,
    lookup_journey_event,
    overcome_the_odds,
    reset_daily_legacy_abilities,
)
from src.llm import ChatProvider
from src.rag import query as rag_query
from src.tools import (
    draw_cards,
    extract_dice_expression,
    format_card_result,
    format_dice_result,
    is_card_plus_rules_question,
    is_card_question,
    is_dice_question,
    roll_dice,
    run_explicit_command,
)

def get_bt_character():
    return character_from_dict(st.session_state.get(character_session_key()))


def _char_id() -> str:
    return active_char_id(st)


def _deck_ctx() -> tuple[str, str | None]:
    return GAME_BRAMBLETREK, _char_id() or None


def brambletrek_shortcut_kwargs() -> dict:
    char = get_bt_character()
    story_mode, card_source = get_play_settings(st)
    return {
        "in_aldwund": char.in_aldwund,
        "reason_band": char.reason_band,
        "active_adventure": char.active_adventure,
        "char_id": _char_id() or None,
        "card_source": card_source,
    }


def maybe_narrator_log(char_id: str, context: str, *, chat_provider: ChatProvider) -> None:
    story_mode, _ = get_play_settings(st)
    if story_mode != "ai_narrator" or not char_id:
        return
    try:
        prose = synthesize_narrator_line(context, chat_provider=chat_provider)
        if prose:
            log_narrative(char_id, prose, char=get_bt_character())
    except Exception:
        pass


def log_user_prompt(char_id: str, prompt: str) -> None:
    if not char_id:
        return
    stripped = prompt.strip()
    if stripped.startswith("@"):
        log_player_action(char_id, stripped, char=get_bt_character())
    elif stripped.startswith("?"):
        from src.games.brambletrek.lonelog import log_oracle

        log_oracle(char_id, stripped, char=get_bt_character())


def persist_bt_character(data: dict) -> None:
    char = character_from_dict(data)
    char.clamp_stats()
    char_id = _char_id()
    if char_id:
        char.id = char_id
    st.session_state[character_session_key()] = character_to_dict(char)
    save_character(char)
    persist_current_session(st)


def journey_event_stat_preview(event: dict) -> str:
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


def stash_pending_journey(run: dict, shortcut_id: str) -> str:
    """Queue journey cards for per-event sheet updates in the sidebar."""
    cards = run.get("journey_cards")
    if not cards or shortcut_id not in ("journey_day", "aldwund_day"):
        return ""
    char = get_bt_character()
    st.session_state[pending_journey_key()] = {
        "cards": cards,
        "applied": [False] * len(cards),
        "depths_trace": journey_depths_trace(cards, start_in_aldwund=char.in_aldwund),
        "shortcut_id": shortcut_id,
    }
    char_id = _char_id()
    if char_id:
        log_draw(char_id, cards, label="Journey draw 4", char=char)
    return (
        "\n\n_Apply each event in the sidebar **Today's draws** when you resolve it "
        "(combat, abilities, and items happen between cards — not all at once)._"
    )


def render_pending_journey_panel(c: dict) -> None:
    pending = st.session_state.get(pending_journey_key())
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

    char = get_bt_character()
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
                extra = journey_event_stat_preview(event)
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
                st.session_state[pending_journey_key()] = pending
                persist_bt_character(character_to_dict(char))
                char_id = _char_id()
                if char_id:
                    preview = journey_event_stat_preview(event or {})
                    log_mechanical(
                        char_id,
                        f"{card_short_label(card)} {preview}",
                        char=char,
                    )
                    log_mechanical(
                        char_id,
                        format_resources(char.health, char.morale, char.supplies),
                        char=char,
                    )
                st.toast(summary.replace("**", ""), icon="✅")
                st.rerun()

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("Finish day", key="bt_finish_journey_day", use_container_width=True):
            char.journey_day = max(1, char.journey_day + 1)
            reset_daily_legacy_abilities(char)
            char.clamp_stats()
            persist_bt_character(character_to_dict(char))
            char_id = _char_id()
            if char_id:
                open_scene(char_id, char)
                log_mechanical(
                    char_id,
                    format_resources(char.health, char.morale, char.supplies),
                    char=char,
                )
            del st.session_state[pending_journey_key()]
            st.rerun()
    with col_b:
        if st.button("Discard draws", key="bt_clear_pending", use_container_width=True):
            del st.session_state[pending_journey_key()]
            st.rerun()

    with st.expander("Quick bulk apply (optional)"):
        st.caption(
            "Applies all remaining non-combat stats at once and does not advance the day. "
            "Inaccurate if you stopped for combat mid-day."
        )
        if st.button("Bulk apply non-combat stats", key="bt_bulk_apply"):
            char_id = _char_id()
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
                if char_id:
                    preview = journey_event_stat_preview(ev or {})
                    log_mechanical(
                        char_id,
                        f"{card_short_label(card)} {preview}",
                        char=char,
                    )
            pending["applied"] = applied
            st.session_state[pending_journey_key()] = pending
            persist_bt_character(character_to_dict(char))
            if char_id:
                log_mechanical(
                    char_id,
                    format_resources(char.health, char.morale, char.supplies),
                    char=char,
                )
            st.rerun()


def select_index(options: list[tuple[str, str]], current: str) -> int:
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


def inject_legacy_ability_styles() -> None:
    global _LEGACY_STYLES_INJECTED
    if not _LEGACY_STYLES_INJECTED:
        st.markdown(_LEGACY_STYLES, unsafe_allow_html=True)
        _LEGACY_STYLES_INJECTED = True


def legacy_tag_html(tags: list[str] | None) -> str:
    if not tags:
        return ""
    parts = []
    for tag in tags:
        cls = f"bt-tag bt-tag-{tag}" if tag in ("combat", "exploration", "universal") else "bt-tag"
        parts.append(f'<span class="{cls}">{tag}</span>')
    return " ".join(parts)


def legacy_ability_header_html(label: str, used: bool, tags: list[str] | None = None) -> str:
    safe_label = html.escape(label)
    name_cls = "bt-ability-name used" if used else "bt-ability-name"
    badge_cls = "bt-badge bt-badge-used" if used else "bt-badge bt-badge-ready"
    badge_text = "Used today" if used else "Ready"
    tag_html = legacy_tag_html(tags)
    return (
        f'<div class="bt-ability-row">'
        f'<span class="{name_cls}">{safe_label}</span>'
        f'<span class="{badge_cls}">{badge_text}</span>'
        f"{tag_html}"
        f"</div>"
    )


def render_legacy_abilities_panel(
    legacy_id: str,
    used_map: dict[str, bool],
) -> dict[str, bool]:
    """Render daily abilities with cards; return updated used_map."""
    inject_legacy_ability_styles()
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
                    f"{legacy_ability_header_html(ab['label'], used_map[ab_id], ab.get('tags'))}"
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
                f"{legacy_ability_header_html(oto['label'], used_map[oto_id], ['universal'])}"
                f'<span class="bt-oto-label">Shared by all Legacies</span>'
                f'<p class="bt-ability-desc">{oto_desc}</p></div>',
                unsafe_allow_html=True,
            )

    return used_map


def render_roster_sidebar() -> None:
    entries = list_characters()
    char_id = _char_id()
    ids = [e.id for e in entries]
    labels = {e.id: e.name for e in entries}

    st.text_input("New character name (optional)", key="bt_new_char_name")

    if ids:
        chosen = st.selectbox(
            "Gnawborn",
            options=ids,
            index=ids.index(char_id) if char_id in ids else 0,
            format_func=lambda cid: labels.get(cid, cid),
            key="bt_roster_select",
        )
        if chosen and chosen != char_id:
            switch_character(st, chosen)
            st.rerun()

    ncol1, ncol2 = st.columns(2)
    with ncol1:
        if st.button("New Gnawborn", key="bt_new_char", use_container_width=True):
            name = st.session_state.get("bt_new_char_name", "")
            new_char = create_character(name)
            switch_character(st, new_char.id)
            st.rerun()
    with ncol2:
        if len(entries) > 1 and st.button("Delete", key="bt_delete_char", use_container_width=True):
            if char_id:
                delete_character(char_id)
                init_brambletrek_session(st)
                st.rerun()

    story_key = play_setting_key(GAME_BRAMBLETREK, "story_mode")
    card_key = play_setting_key(GAME_BRAMBLETREK, "card_source")
    story_labels = {"player": "Player-led", "ai_narrator": "AI narrator"}
    card_labels = {"physical": "Physical deck", "virtual": "Virtual (AI draws)"}
    story_opts = list(story_labels.keys())
    card_opts = list(card_labels.keys())
    current_settings = get_play_settings(st)
    st.radio(
        "Story mode",
        options=story_opts,
        index=story_opts.index(current_settings.get("story_mode", "player")),
        format_func=lambda k: story_labels[k],
        key=story_key,
        help="Player-led: you write @ actions; AI narrator adds => consequences after events.",
    )
    st.radio(
        "Card source",
        options=card_opts,
        index=card_opts.index(current_settings.get("card_source", "virtual")),
        format_func=lambda k: card_labels[k],
        key=card_key,
        help="Physical: report cards from your real deck (synced to virtual deck).",
    )
    persist_current_session(st)


def render_lonelog_sidebar() -> None:
    char_id = _char_id()
    if not char_id:
        return
    with st.expander("Lonelog", expanded=False):
        tail = read_tail(char_id, n_lines=30)
        if tail:
            st.code("\n".join(tail), language=None)
        else:
            st.caption("No log entries yet. Draws, @ actions, and journey events append here.")
        path = log_path(char_id)
        if path.exists():
            st.download_button(
                "Download log",
                data=path.read_text(encoding="utf-8"),
                file_name=f"lonelog_{char_id}.md",
                mime="text/markdown",
                key="bt_lonelog_download",
            )


def render_character_sidebar() -> None:
    render_roster_sidebar()
    st.subheader("Your Gnawborn")
    c = dict(st.session_state[character_session_key()])

    c["name"] = st.text_input("Name", value=c.get("name", ""), key="bt_name")

    reason_opts = table_options("reasons")
    c["reason_band"] = st.selectbox(
        "Reason for adventure",
        options=[o[0] for o in reason_opts],
        index=select_index(reason_opts, c.get("reason_band", "")),
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
        index=select_index(bg_opts, c.get("background_band", "")),
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
        index=select_index(trinket_opts, c.get("trinket_band", "")),
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
        index=select_index([(i, legacy_opts[i]["label"]) for i in legacy_ids], c.get("legacy", "")),
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
        inject_legacy_ability_styles()
        prev_legacy = st.session_state.get("bt_last_legacy")
        used_map: dict[str, bool] = dict(c.get("legacy_abilities_used") or {})
        if prev_legacy is not None and prev_legacy != c["legacy"]:
            used_map = {}
        st.session_state.bt_last_legacy = c["legacy"]

        used_map = render_legacy_abilities_panel(c["legacy"], used_map)

        c["legacy_abilities_used"] = used_map
        if st.button(
            "Reset daily abilities",
            key="bt_reset_abilities",
            type="secondary",
            use_container_width=True,
        ):
            c["legacy_abilities_used"] = {}
            st.rerun()

    render_pending_journey_panel(c)

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
        index=select_index(adv_opts, c.get("active_adventure", "")),
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

    render_lonelog_sidebar()

    persist_bt_character(c)

    if st.button("Reset character", key="bt_reset"):
        char_id = _char_id()
        reset = default_character()
        if char_id:
            reset.id = char_id
        st.session_state[character_session_key()] = character_to_dict(reset)
        save_character(reset)
        st.rerun()


def answer_table_lookup_prompt(
    prompt: str,
    *,
    game_id: str,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider = "ollama",
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
        brambletrek_character=get_bt_character() if game_id == GAME_BRAMBLETREK else None,
        chat_provider=chat_provider,
    )
    return result.answer, result.sources, "rag"


def execute_brambletrek_shortcut_answer(
    shortcut_id: str,
    *,
    mode: str,
    game_id: str,
    game_state,
    prior_history: list[dict[str, str]],
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider = "ollama",
) -> tuple[str, list[dict], str]:
    """Run a matched shortcut and return (answer, sources, route)."""
    run = run_shortcut(shortcut_id, game_id=game_id, **brambletrek_shortcut_kwargs())
    kind = run["kind"]
    route = f"brambletrek:{shortcut_id}"

    if kind in {"multi_draw_rag", "rag_only", "roll_rag"}:
        answer, sources, _ = answer_table_lookup_prompt(
            run["prompt"],
            game_id=game_id,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
            chat_provider=chat_provider,
        )
        if kind in {"multi_draw_rag", "roll_rag"}:
            stat_note = stash_pending_journey(run, shortcut_id)
            answer = f"{run['user_message']}{stat_note}\n\n{answer}"
            maybe_narrator_log(_char_id(), answer, chat_provider=chat_provider)
        refresh_deck(*_deck_ctx())
        return answer, sources, route

    out = run_agent(
        run["prompt"],
        history=to_langchain_history(prior_history),
        game_state=game_state,
        game_id=game_id,
        retrieval=retrieval_cfg,
        brambletrek_character=st.session_state.get(character_session_key()),
        chat_provider=chat_provider,
        char_id=_char_id() or None,
        story_mode=get_play_settings(st)[0],
        card_source=get_play_settings(st)[1],
    )
    refresh_deck(*_deck_ctx())
    return out["answer"], out.get("sources", []), route


def run_brambletrek_shortcut(
    shortcut_id: str,
    *,
    mode: str,
    game_id: str,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider = "ollama",
) -> None:
    sync_deck(*_deck_ctx())
    run = run_shortcut(shortcut_id, game_id=game_id, **brambletrek_shortcut_kwargs())
    prior_history = recent_chat_history()
    st.session_state.messages.append({"role": "user", "content": run["user_message"]})

    kind = run["kind"]
    if kind in {"multi_draw_rag", "rag_only", "roll_rag"}:
        answer, sources, _route = answer_table_lookup_prompt(
            run["prompt"],
            game_id=game_id,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
            chat_provider=chat_provider,
        )
        if kind in {"multi_draw_rag", "roll_rag"}:
            stat_note = stash_pending_journey(run, shortcut_id)
            answer = f"{run['user_message']}{stat_note}\n\n{answer}"
            maybe_narrator_log(_char_id(), answer, chat_provider=chat_provider)
    else:
        out = run_agent(
            run["prompt"],
            history=to_langchain_history(prior_history),
            game_state=None,
            game_id=game_id,
            retrieval=retrieval_cfg,
            brambletrek_character=st.session_state.get(character_session_key()),
            chat_provider=chat_provider,
            char_id=_char_id() or None,
            story_mode=get_play_settings(st)[0],
            card_source=get_play_settings(st)[1],
        )
        answer, sources = out["answer"], out.get("sources", [])

    refresh_deck(*_deck_ctx())
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_sources = sources
    st.rerun()


def render_shortcuts(
    game_id: str,
    *,
    mode: str,
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider = "ollama",
) -> None:
    st.subheader("Brambletrek shortcuts")
    char = get_bt_character()
    active_adv = char.active_adventure or ""
    st.caption(
        "Core Hyhill journey uses curated tables (pp. 24–27). "
        "With an active adventure, use **Adventure scene** — scenes from the PDF via RAG."
    )

    for shortcut in shortcuts_for_character(active_adventure=active_adv):
        sid = shortcut["id"]
        if st.button(shortcut["label"], key=f"bt_shortcut_{sid}"):
            run_brambletrek_shortcut(
                sid,
                mode=mode,
                game_id=game_id,
                retrieval_cfg=retrieval_cfg,
                top_k=top_k,
                selected_factions=selected_factions,
                chat_provider=chat_provider,
            )


def init_session_character() -> None:
    init_brambletrek_session(st)


def render_header() -> None:
    st.caption(
        "Personal study helper. You run the story and dice; the assistant helps "
        "interpret rule text and what roll results mean."
    )
    bt_char = get_bt_character()
    char_summary = format_character_summary(bt_char)
    if char_summary:
        st.info(char_summary)
    stat_cols = st.columns(4)
    stat_cols[0].metric("Health", bt_char.health)
    stat_cols[1].metric("Morale", bt_char.morale)
    stat_cols[2].metric("Supplies", bt_char.supplies)
    stat_cols[3].metric("Journey day", bt_char.journey_day)


def chat_placeholder() -> str:
    return "Journey, @ action, rules… or /day, /roll d20, /log line, /deck reset"


def try_handle_prompt(
    prompt: str,
    *,
    mode: str,
    game_id: str,
    prior_history: list[dict[str, str]],
    retrieval_cfg: dict,
    top_k: int,
    selected_factions: list[str] | None,
    chat_provider: ChatProvider = "ollama",
) -> tuple[str, list[dict], str] | None:
    """Return answer if Brambletrek handled the prompt, else None."""
    stripped = prompt.strip().lower()
    if stripped in {"/day", "/journey"}:
        day_shortcut = (
            "adventure_scene"
            if (get_bt_character().active_adventure or "")
            else "journey_day"
        )
        return execute_brambletrek_shortcut_answer(
            day_shortcut,
            mode=mode,
            game_id=game_id,
            game_state=None,
            prior_history=prior_history,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
            chat_provider=chat_provider,
        )
    shortcut_id = match_brambletrek_shortcut(
        prompt,
        active_adventure=get_bt_character().active_adventure or "",
    )
    if shortcut_id:
        return execute_brambletrek_shortcut_answer(
            shortcut_id,
            mode=mode,
            game_id=game_id,
            game_state=None,
            prior_history=prior_history,
            retrieval_cfg=retrieval_cfg,
            top_k=top_k,
            selected_factions=selected_factions,
            chat_provider=chat_provider,
        )
    return None
