"""Apothecaria shortcuts."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

from src.games.apothecaria.curated import (
    all_purchasable_tools,
    all_upgrades,
    festival_for_season,
    foraging_rules_text,
    format_ailment_draw,
    format_familiar_skill_draw,
    format_familiar_type_draw,
    format_forage_draw,
    format_patient_type_draw,
    format_witch_clue_draw,
    locale_meta,
    locale_options,
    lookup_reagent,
    reagents_for_tags,
    reputation_tier_label,
    village_services,
)
from src.games.apothecaria.cottage import WitchCottage
from src.games.apothecaria.game_logic import (
    advance_downtime,
    advance_week,
    buy_tool,
    buy_upgrade,
    can_access_locale,
    change_locale,
    compute_payment,
    foraging_points_for_locale,
    potion_totals,
    resolve_hunt_step,
    set_hunt_target,
    start_ailment,
)
from src.play_tools import draw_cards

GAME_APOTHECARIA = "apothecaria"

ShortcutKind = Literal["draw", "static", "rag_only", "action"]


class ApothecariaShortcut(TypedDict):
    id: str
    label: str
    kind: ShortcutKind


_BASE_SHORTCUTS: list[ApothecariaShortcut] = [
    {"id": "start_patient", "label": "New patient (2 cards)", "kind": "draw"},
    {"id": "draw_patient_type", "label": "Draw patient type", "kind": "draw"},
    {"id": "draw_ailment", "label": "Draw ailment", "kind": "draw"},
    {"id": "change_locale", "label": "Change locale", "kind": "action"},
    {"id": "forage_event", "label": "Forage / draw event", "kind": "draw"},
    {"id": "hunt_reagent", "label": "Hunt reagent", "kind": "action"},
    {"id": "potion_preview", "label": "Preview potion payment", "kind": "static"},
    {"id": "complete_potion", "label": "Complete potion", "kind": "action"},
    {"id": "advance_downtime", "label": "Spend downtime segment", "kind": "action"},
    {"id": "advance_week", "label": "Advance week", "kind": "action"},
    {"id": "festival_prompts", "label": "Festival prompts", "kind": "static"},
    {"id": "village_services", "label": "Village services", "kind": "static"},
    {"id": "shop_tools", "label": "Tool shop", "kind": "static"},
    {"id": "shop_upgrades", "label": "Cottage upgrades", "kind": "static"},
    {"id": "buy_tool", "label": "Buy tool", "kind": "action"},
    {"id": "buy_upgrade", "label": "Buy upgrade", "kind": "action"},
    {"id": "witch_clue", "label": "Witch mystery clue", "kind": "draw"},
    {"id": "draw_familiar_type", "label": "Draw familiar form", "kind": "draw"},
    {"id": "draw_familiar_skill", "label": "Draw familiar skill", "kind": "draw"},
    {"id": "foraging_rules", "label": "Foraging rules", "kind": "static"},
    {"id": "locales_help", "label": "Locales overview", "kind": "rag_only"},
    {"id": "reagents_help", "label": "Reagents & tags help", "kind": "rag_only"},
]

SHORTCUTS: list[ApothecariaShortcut] = list(_BASE_SHORTCUTS)
SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def shortcuts_for_cottage(
    *,
    phase: str = "idle",
    has_ailment: bool = False,
    has_hunt: bool = False,
    has_inventory: bool = False,
) -> list[ApothecariaShortcut]:
    out: list[ApothecariaShortcut] = []
    for s in SHORTCUTS:
        sid = s["id"]
        if sid in ("start_patient", "draw_patient_type", "draw_ailment"):
            if phase in ("idle", "downtime", "festival") and not has_ailment:
                out.append(s)
            continue
        if sid in ("change_locale", "forage_event", "hunt_reagent", "reagents_help"):
            if phase == "ailment" or has_ailment:
                out.append(s)
            continue
        if sid in ("potion_preview", "complete_potion"):
            if has_ailment or has_inventory:
                out.append(s)
            continue
        if sid == "advance_downtime":
            if phase == "downtime":
                out.append(s)
            continue
        if sid in ("advance_week", "festival_prompts"):
            if phase in ("idle", "downtime", "festival"):
                out.append(s)
            continue
        if sid in ("village_services", "shop_tools", "shop_upgrades", "buy_tool", "buy_upgrade"):
            if phase in ("idle", "downtime", "festival"):
                out.append(s)
            continue
        if sid == "witch_clue":
            if phase in ("idle", "downtime", "ailment"):
                out.append(s)
            continue
        if sid in ("draw_familiar_type", "draw_familiar_skill"):
            if phase in ("idle", "downtime"):
                out.append(s)
            continue
        if sid in ("foraging_rules", "locales_help"):
            out.append(s)
    return out


def match_apothecaria_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if any(p in lower for p in ("new patient", "start patient", "begin patient")):
        return "start_patient"
    if any(p in lower for p in ("patient type", "draw patient", "who is the patient")):
        return "draw_patient_type"
    if any(p in lower for p in ("draw ailment", "diagnose", "what ailment")):
        return "draw_ailment"
    if any(p in lower for p in ("change locale", "travel to", "go to glimmerwood")):
        return "change_locale"
    if any(p in lower for p in ("forage", "locale event", "foraging event")):
        return "forage_event"
    if "hunt reagent" in lower or "hunt for" in lower:
        return "hunt_reagent"
    if "complete potion" in lower or "finish potion" in lower:
        return "complete_potion"
    if "preview potion" in lower or "potion payment" in lower:
        return "potion_preview"
    if "downtime" in lower and ("spend" in lower or "segment" in lower):
        return "advance_downtime"
    if "advance week" in lower or "next week" in lower:
        return "advance_week"
    if "festival" in lower:
        return "festival_prompts"
    if "village" in lower and "service" in lower:
        return "village_services"
    if "tool shop" in lower or "buy tool" in lower:
        return "shop_tools"
    if "upgrade" in lower and "shop" in lower:
        return "shop_upgrades"
    if "familiar form" in lower or "familiar type" in lower:
        return "draw_familiar_type"
    if "familiar skill" in lower:
        return "draw_familiar_skill"
    if "witch clue" in lower or "witch mystery" in lower:
        return "witch_clue"
    if "foraging rules" in lower or "how to forage" in lower:
        return "foraging_rules"
    if "locales" in lower and ("overview" in lower or "list" in lower):
        return "locales_help"
    if "reagent" in lower and ("tag" in lower or "help" in lower):
        return "reagents_help"
    return None


def _draw(game_id: str, char_id: str | None, card_source: str, count: int = 1) -> list[str]:
    if card_source == "physical":
        raise ValueError("Physical deck mode: report your cards in chat or switch to virtual deck.")
    result = draw_cards(count=count, game_id=game_id, char_id=char_id)
    if not result.get("ok"):
        raise ValueError(result.get("error") or "Draw failed")
    return list(result.get("cards") or [])


def _cottage_state(cottage: WitchCottage | dict | None) -> WitchCottage:
    if isinstance(cottage, WitchCottage):
        return cottage
    if isinstance(cottage, dict):
        from src.games.apothecaria.cottage import cottage_from_dict

        return cottage_from_dict(cottage)
    from src.games.apothecaria.cottage import default_cottage

    return default_cottage()


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_APOTHECARIA,
    char_id: str | None = None,
    card_source: str = "virtual",
    reputation: int = 5,
    current_locale: str = "glimmerwood",
    ailment_tags: list[str] | None = None,
    cottage: WitchCottage | dict | None = None,
    locale_id: str | None = None,
    reagent_name: str | None = None,
    tool_id: str | None = None,
    upgrade_id: str | None = None,
    cards: list[str] | None = None,
) -> dict[str, Any]:
    state = _cottage_state(cottage)
    state.reputation = reputation
    if current_locale:
        state.current_locale = current_locale

    if shortcut_id == "foraging_rules":
        msg = foraging_rules_text()
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "locales_help":
        lines = ["**Locales in High Rannoc**", ""]
        meta = locale_meta()
        for loc in locale_options():
            lid = loc["id"]
            unlock = (meta.get(lid) or {}).get("unlock")
            lock = f" (needs {unlock})" if unlock else ""
            accessible = can_access_locale(state, lid)
            flag = "" if accessible else " 🔒"
            lines.append(f"- **{loc['label']}** (`{lid}`){lock}{flag}")
        msg = "\n".join(lines)
        prompt = (
            "Summarize Apothecaria locales: how to reach them, what foraging involves, "
            "and travel tools (coracle, broom, portal)."
        )
        return {"user_message": msg, "prompt": prompt}

    if shortcut_id == "reagents_help":
        tags = ailment_tags or list(state.ailment_tags)
        if tags:
            matches = []
            for reg in reagents_for_tags(tags):
                name = reg.get("name", "")
                locales = reg.get("locales") or {}
                loc_bits = ", ".join(f"{k} ({v})" for k, v in list(locales.items())[:3])
                preps = ", ".join(reg.get("preparations") or [])
                matches.append(f"- **{name}** — {loc_bits} · {preps}")
            body = "\n".join(matches[:12]) if matches else "_No curated matches; search rules for tag._"
            msg = f"**Reagents for tags** {', '.join(f'[{t}]' for t in tags)}\n\n{body}"
        else:
            msg = "**Reagents** — draw an ailment first, or ask about a specific [TAG] in chat."
        prompt = (
            "Explain how Apothecaria reagents work: PLANT/ANIMAL/MAGIC types, locales, "
            "Foraging Values, preparation (CRUSH/BOIL/DISTIL/RAW), Poison and Sweet points."
        )
        return {"user_message": msg, "prompt": prompt}

    if shortcut_id == "village_services":
        lines = ["**Village services**", ""]
        for svc in village_services():
            req = svc.get("requires")
            req_str = f" (requires {req})" if req else ""
            lines.append(f"- **{svc.get('name')}** — {svc.get('effect', '')}{req_str}")
        msg = "\n".join(lines)
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "shop_tools":
        lines = ["**Bits & Bobs — tools**", ""]
        for tool in all_purchasable_tools():
            owned = " ✓" if tool.get("id") in state.tools_owned else ""
            lines.append(f"- `{tool.get('id')}` **{tool.get('name')}** — {tool.get('cost')} Silver{owned}")
            lines.append(f"  _{tool.get('effect', '')}_")
        msg = "\n".join(lines)
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "shop_upgrades":
        lines = ["**Cottage upgrades**", ""]
        for up in all_upgrades():
            owned = " ✓" if up.get("id") in state.upgrades_owned else ""
            rep = f", rep {up['rep_min']}+" if up.get("rep_min") else ""
            lines.append(f"- `{up.get('id')}` **{up.get('name')}** — {up.get('cost')} Silver{rep}{owned}")
            lines.append(f"  _{up.get('effect', '')}_")
        msg = "\n".join(lines)
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "festival_prompts":
        fest = festival_for_season(state.season)
        lines = [f"**{fest.get('name', state.season.title() + ' festival')}**", ""]
        for i, prompt in enumerate(fest.get("prompts") or [], 1):
            lines.append(f"{i}. {prompt}")
        msg = "\n".join(lines)
        return {"user_message": msg, "prompt": msg, "static": True}

    if shortcut_id == "potion_preview":
        poison, sweet = potion_totals(state)
        pay = compute_payment(state, poison, sweet)
        msg = (
            f"**Potion preview**\n\n"
            f"Poison {poison} · Sweet {sweet}\n"
            f"Base {pay['base']} Silver → **{pay['silver']} Silver**"
            f"{' (REJECTED)' if pay['rejected'] else ''}"
        )
        return {"user_message": msg, "prompt": msg, "static": True, "payment": pay}

    if shortcut_id == "change_locale":
        target = locale_id or state.current_locale
        if target == state.current_locale:
            raise ValueError("Already at that locale.")
        result = change_locale(state, target)
        label = next((l["label"] for l in locale_options() if l["id"] == target), target)
        msg = f"**Travelled** to **{label}** (`{target}`)."
        if result.get("timer") is not None:
            msg += f" Timer now {result['timer']}."
        return {"user_message": msg, "prompt": msg, "static": True, "state_change": result}

    if shortcut_id == "hunt_reagent":
        name = reagent_name
        if not name:
            tags = ailment_tags or list(state.ailment_tags)
            matches = reagents_for_tags(tags, limit=1)
            if not matches:
                raise ValueError("No reagent name given and no ailment tags to match.")
            name = str(matches[0].get("name", ""))
        result = set_hunt_target(state, name)
        reg = lookup_reagent(name) or {}
        msg = (
            f"**Hunting {name}** ({reg.get('type', '?')})\n\n"
            f"Locale: `{result['locale']}` · Foraging value **{result['foraging_value']}**"
        )
        return {"user_message": msg, "prompt": msg, "static": True, "hunt": result}

    if shortcut_id == "buy_tool":
        if not tool_id:
            raise ValueError("Specify tool_id (see Tool shop).")
        result = buy_tool(state, tool_id)
        msg = f"**Purchased {result['name']}** for {result['cost']} Silver. Balance: {result['silver']}."
        return {"user_message": msg, "prompt": msg, "static": True, "purchase": result}

    if shortcut_id == "buy_upgrade":
        if not upgrade_id:
            raise ValueError("Specify upgrade_id (see Cottage upgrades).")
        result = buy_upgrade(state, upgrade_id)
        msg = f"**Built {result['name']}** for {result['cost']} Silver. Balance: {result['silver']}."
        return {"user_message": msg, "prompt": msg, "static": True, "purchase": result}

    if shortcut_id == "complete_potion":
        poison, sweet = potion_totals(state)
        pay = compute_payment(state, poison, sweet)
        from src.games.apothecaria.game_logic import complete_potion

        result = complete_potion(state, poison, sweet)
        msg = (
            f"**Potion delivered** for {result.get('cleared_ailment') or 'patient'}\n\n"
            f"+{result['silver_gained']} Silver"
            f"{' · Reputation ' + ('+1' if result['reputation_delta'] > 0 else str(result['reputation_delta'])) if result['reputation_delta'] else ''}"
            f"{' · REJECTED (too poisonous)' if result['rejected'] else ''}\n\n"
            f"Downtime begins (6 segments)."
        )
        return {"user_message": msg, "prompt": msg, "static": True, "completion": result, "payment": pay}

    if shortcut_id == "advance_downtime":
        result = advance_downtime(state)
        msg = (
            f"**Downtime** — {result['remaining']} segments left."
            if not result["done"]
            else "**Downtime over.** Ready for the next patient."
        )
        return {"user_message": msg, "prompt": msg, "static": True, "downtime": result}

    if shortcut_id == "advance_week":
        result = advance_week(state, downtime=state.phase == "downtime")
        fest = f" **{result['season'].title()} festival!**" if result.get("festival") else ""
        msg = f"**Week {result['week']}** of {result['season']}.{fest}"
        return {"user_message": msg, "prompt": msg, "static": True, "calendar": result}

    if shortcut_id == "start_patient":
        drawn = cards or _draw(game_id, char_id, card_source, 2)
        patient = format_patient_type_draw(drawn[0])
        ailment = format_ailment_draw(drawn[1], state.reputation)
        start_ailment(
            state,
            ailment_name=str(ailment.get("name", "")),
            tags=list(ailment.get("tags") or []),
            timer=ailment.get("timer"),
            patient_type=str(patient.get("patient_type", "")),
        )
        timer = ailment.get("timer")
        user = (
            f"**New patient**\n\n"
            f"Type: {patient.get('summary', '')}\n"
            f"Ailment: {ailment.get('summary', '')}\n\n"
            f"{ailment.get('description', '')}"
        )
        if ailment.get("consequence"):
            user += f"\n\n_Consequence if the timer runs out:_ {ailment['consequence']}"
        prompt = (
            f"New patient arrives: {patient.get('patient_type')} with {ailment.get('name')} "
            f"(tags {ailment.get('tags')}, timer {timer}). "
            f"{ailment.get('description', '')} "
            f"Write a journal scene as the witch meets them and considers the cure."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "cards": drawn,
            "draw_result": {"patient": patient, "ailment": ailment},
        }

    card = (cards or _draw(game_id, char_id, card_source, 1))[0]

    if shortcut_id == "draw_patient_type":
        result = format_patient_type_draw(card)
        user = f"**Patient type draw:** {card}\n\n{result.get('summary', '')}"
        return {"user_message": user, "prompt": user, "cards": [card], "draw_result": result, "static": True}

    if shortcut_id == "draw_ailment":
        result = format_ailment_draw(card, state.reputation)
        tier = result.get("tier", "")
        user = (
            f"**Ailment draw** ({reputation_tier_label(state.reputation)}, rep {state.reputation}): {card}\n\n"
            f"{result.get('summary', '')}\n\n{result.get('description', '')}"
        )
        if result.get("consequence"):
            user += f"\n\n_Consequence if the timer runs out:_ {result['consequence']}"
        prompt = (
            f"Diagnosis: {result.get('name')} (tags {result.get('tags')}, timer {result.get('timer')}). "
            f"{result.get('description', '')} "
            f"Write a journal scene as the witch examines the patient and plans the cure."
        )
        return {"user_message": user, "prompt": prompt, "cards": [card], "draw_result": result}

    if shortcut_id == "forage_event":
        result = resolve_hunt_step(state, card)
        event = str(result.get("event", ""))
        user = f"**Forage:** {result.get('summary', card)}\n\n{event}"
        if result.get("found"):
            found_name = result.get("found_reagent") or result.get("target")
            user += f"\n\n✓ Found **{found_name}**!"
        elif state.hunting_reagent or result.get("target"):
                user += (
                    f"\n\nHunting **{result.get('target')}** (FV {result.get('target_fv')}) — "
                    f"points now **{result.get('foraging_points')}**"
                )
        if result.get("event_repeat"):
            user += "\n\n_(Repeat event — no timer cost.)_"
        prompt = (
            f"Foraging in {result.get('locale_label')}. Card {card} (value {result.get('numeric_value')}). "
            f"Event: {event}. "
            f"Write a journal scene of the witch foraging — the place, the moment, what happens."
        )
        return {"user_message": user, "prompt": prompt, "cards": [card], "draw_result": result}

    if shortcut_id == "witch_clue":
        result = format_witch_clue_draw(card, state.storyline_table)
        user = f"**Witch clue:** {card}\n\n{result.get('summary', '')}"
        prompt = (
            f"Witch mystery clue ({state.storyline_table}): {result.get('clue')}. "
            f"Write a journal scene of discovering this clue about the cottage's previous witch."
        )
        return {"user_message": user, "prompt": prompt, "cards": [card], "draw_result": result}

    if shortcut_id == "draw_familiar_type":
        result = format_familiar_type_draw(card)
        user = f"**Familiar form:** {card}\n\n{result.get('summary', '')}"
        return {"user_message": user, "prompt": user, "cards": [card], "draw_result": result, "static": True}

    if shortcut_id == "draw_familiar_skill":
        result = format_familiar_skill_draw(card)
        user = f"**Familiar skill:** {card}\n\n{result.get('summary', '')}"
        return {"user_message": user, "prompt": user, "cards": [card], "draw_result": result, "static": True}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
