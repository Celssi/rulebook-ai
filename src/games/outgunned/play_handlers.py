"""Outgunned play handlers (GmSoloHandlers)."""

from __future__ import annotations

from typing import Any

from src.games.gm_solo.game_handlers import GmSoloHandlers
from src.games.outgunned.actions import (
    SHORTCUTS,
    SHORTCUT_IDS,
    match_outgunned_shortcut,
    run_shortcut,
)
from src.games.outgunned.character import (
    OutgunnedHero,
    character_options_payload,
    format_for_prompt,
    format_summary,
    hero_from_dict,
    hero_to_dict,
    default_hero,
)
from src.games.outgunned.lonelog import log_draw, read_tail
from src.games.outgunned.narrator import synthesize_journal_entry
from src.games.saves import PlayContext

GAME_ID = "outgunned"

_NARRATOR_SHORTCUTS = frozenset({"ad_prompt", "outgunned_roll"})


def _shortcut_kwargs(ctx: PlayContext) -> dict:
    hero = hero_from_dict(ctx.entity or {})
    return {
        "hero_name": hero.name,
        "mission_title": hero.mission_title,
        "pool_dice": hero.pool_dice_count(),
        "death_roulette_bullets": hero.death_roulette_bullets,
        "ad_state": dict(hero.ad_state),
    }


def _apply_shortcut_state(ctx: PlayContext, run: dict, hero: OutgunnedHero) -> None:
    if run.get("mission_title"):
        hero.mission_title = str(run["mission_title"])
    patch = run.get("ad_state_patch")
    if isinstance(patch, dict):
        hero.ad_state.update(patch)
    ad_prompt = run.get("ad_prompt")
    if isinstance(ad_prompt, dict) and ad_prompt.get("text"):
        hero.last_prompt = str(ad_prompt["text"])
    if run.get("hurdle"):
        hero.ad_state["hurdle"] = str(run["hurdle"])
    if run.get("roll_summary"):
        hero.last_roll_summary = str(run["roll_summary"])
    if "death_roulette_bullets" in run:
        hero.death_roulette_bullets = int(run["death_roulette_bullets"])
    task = run.get("task")
    if task:
        hero.ad_state["last_task"] = str(task)


HANDLERS = GmSoloHandlers(
    game_id=GAME_ID,
    entity_from_dict=hero_from_dict,
    entity_to_dict=hero_to_dict,
    default_entity=default_hero,
    format_summary=format_summary,
    format_for_prompt=format_for_prompt,
    shortcuts=SHORTCUTS,
    shortcut_ids=SHORTCUT_IDS,
    match_shortcut=match_outgunned_shortcut,
    run_shortcut=run_shortcut,
    shortcut_kwargs=_shortcut_kwargs,
    apply_shortcut_state=_apply_shortcut_state,
    narrator_shortcuts=_NARRATOR_SHORTCUTS,
    synthesize_journal=synthesize_journal_entry,
    log_draw=log_draw,
    read_lonelog_tail=read_tail,
    character_options=character_options_payload,
    gm_role="Assistant Director",
)

# Re-export for API service
def persist_character(ctx: PlayContext, data: dict | None = None) -> dict:
    raw = data if data is not None else ctx.entity or {}
    prior = hero_from_dict(ctx.entity or {})
    hero = hero_from_dict(raw)
    if hero.role and hero.role != prior.role:
        hero.apply_role(hero.role)
        if hero.trope:
            hero.apply_trope(hero.trope)
    elif hero.trope and hero.trope != prior.trope and hero.role:
        hero.apply_role(hero.role)
        hero.apply_trope(hero.trope)
    return HANDLERS.persist_character(ctx, hero_to_dict(hero))


character_header = HANDLERS.character_header
reset_character = HANDLERS.reset_character
get_character = HANDLERS.get_character
character_options_payload = HANDLERS.character_options_payload
roster_payload = HANDLERS.roster_payload
create_character_entry = HANDLERS.create_character_entry
delete_character_entry = HANDLERS.delete_character_entry
switch_character = HANDLERS.switch_character
execute_shortcut = HANDLERS.execute_shortcut
try_handle_prompt = HANDLERS.try_handle_prompt
shortcuts_payload = HANDLERS.shortcuts_payload
lonelog_tail = HANDLERS.lonelog_tail
append_chat_exchange = HANDLERS.append_chat_exchange
entity_for_rag = HANDLERS.entity_for_rag
log_user_prompt = HANDLERS.log_user_prompt
run_character_shortcut = HANDLERS.run_character_shortcut
