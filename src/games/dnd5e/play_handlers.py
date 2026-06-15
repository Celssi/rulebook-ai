"""D&D 5e play handlers (GmSoloHandlers)."""

from __future__ import annotations

from src.games.dnd5e.actions import SHORTCUT_IDS, SHORTCUTS, match_dnd5e_shortcut, run_shortcut
from src.games.dnd5e.entity import (
    Dnd5eCharacter,
    character_from_dict,
    character_to_dict,
    default_character,
    format_for_prompt,
    format_summary,
)
from src.games.dnd5e.character_builder import character_creation_summary, level_up, rebuild_character
from src.games.dnd5e.character_data import character_options_payload as dnd_character_options
from src.games.dnd5e.lonelog import log_narrative_line, log_roll, narrative_context_for_ai, read_tail
from src.games.dnd5e.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.gm_solo.handlers import persist_entity
from src.games.gm_solo.game_handlers import GmSoloHandlers
from src.games.saves import PlayContext

GAME_ID = "dnd5e"

_NARRATOR_SHORTCUTS = frozenset(
    {"ability_check", "saving_throw", "attack_roll", "death_save"}
)


_ROLL_PARAM_KEYS = frozenset({"target_ac", "ability", "advantage", "modifier", "proficient", "hit_dice_to_spend"})


def _shortcut_kwargs(ctx: PlayContext, params: dict | None = None) -> dict:
    char = character_from_dict(ctx.entity or {})
    kw = {
        "name": char.name,
        "species": char.species,
        "class_name": char.class_name,
        "level": char.level,
        "hp": char.hp,
        "max_hp": char.max_hp,
        "ac": char.ac,
        "hit_die": char.hit_die,
        "hit_dice_max": char.hit_dice_max,
        "hit_dice_spent": char.hit_dice_spent,
        "ability_scores": dict(char.ability_scores),
        "spell_slots": dict(char.spell_slots),
        "death_save_successes": char.death_save_successes,
        "death_save_failures": char.death_save_failures,
    }
    if params:
        for key in _ROLL_PARAM_KEYS:
            if key in params and params[key] is not None:
                kw[key] = params[key]
    return kw


def _apply_shortcut_state(ctx: PlayContext, run: dict, entity: Dnd5eCharacter) -> None:
    updates = run.get("entity_updates")
    if isinstance(updates, dict):
        for key, value in updates.items():
            if hasattr(entity, key):
                setattr(entity, key, value)
        entity.clamp()
    dice = run.get("dice")
    if isinstance(dice, dict) and dice.get("summary"):
        entity.last_roll_summary = str(dice["summary"])[:200]
    else:
        entity.last_roll_summary = str(run.get("user_message", ""))[:200]


def _synthesize(mechanics: str, *, entity: Dnd5eCharacter, chat_provider) -> str | None:
    story_so_far = (
        narrative_context_for_ai(
            entity.id,
            campaign_setting=entity.campaign_setting,
            campaign_notes=entity.campaign_notes,
        )
        if entity.id
        else ""
    )
    prose = synthesize_journal_entry(
        mechanics,
        entity=entity,
        story_so_far=story_so_far,
        chat_provider=chat_provider,
    )
    if prose and entity.id:
        try:
            summary = synthesize_lonelog_summary(prose, chat_provider=chat_provider)
            if summary:
                log_narrative_line(entity.id, summary)
        except Exception:
            pass
    return prose


def _log_draw(slot_id: str, label: str, cards: list[str] | None) -> None:
    _ = cards
    log_roll(slot_id, label, label)


def _persist_character(ctx: PlayContext, data: dict | None = None) -> dict:
    raw = data if data is not None else ctx.entity or {}
    entity = character_from_dict(raw)
    recompute = bool(raw.get("rebuild_stats")) or entity.max_hp <= 0
    entity = rebuild_character(entity, recompute_hp=recompute)
    return persist_entity(ctx, GAME_ID, character_to_dict, entity)


def _character_options() -> dict:
    return dnd_character_options()


HANDLERS = GmSoloHandlers(
    game_id=GAME_ID,
    entity_from_dict=character_from_dict,
    entity_to_dict=character_to_dict,
    default_entity=default_character,
    format_summary=format_summary,
    format_for_prompt=format_for_prompt,
    shortcuts=SHORTCUTS,
    shortcut_ids=SHORTCUT_IDS,
    match_shortcut=match_dnd5e_shortcut,
    run_shortcut=run_shortcut,
    shortcut_kwargs=_shortcut_kwargs,
    apply_shortcut_state=_apply_shortcut_state,
    narrator_shortcuts=_NARRATOR_SHORTCUTS,
    synthesize_journal=_synthesize,
    log_draw=_log_draw,
    read_lonelog_tail=read_tail,
    character_options=_character_options,
    gm_role="Dungeon Master",
)

character_header = HANDLERS.character_header
persist_character = _persist_character
reset_character = HANDLERS.reset_character
character_options_payload = HANDLERS.character_options_payload


def level_up_character(ctx: PlayContext, *, hp_roll: int | None = None) -> dict:
    char = rebuild_character(character_from_dict(ctx.entity or {}))
    char = level_up(char, hp_roll=hp_roll)
    return persist_entity(ctx, GAME_ID, character_to_dict, char)


def rebuild_character_payload(ctx: PlayContext, data: dict | None = None) -> dict:
    return _persist_character(ctx, data)


def creation_summary(ctx: PlayContext) -> dict:
    char = character_from_dict(ctx.entity or {})
    return character_creation_summary(char)


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
