"""Cosmere play handlers (GmSoloHandlers)."""

from __future__ import annotations

from src.games.cosmere.actions import SHORTCUT_IDS, SHORTCUTS, match_cosmere_shortcut, run_shortcut
from src.games.cosmere.entity import (
    CosmereCharacter,
    character_from_dict,
    character_options_payload,
    character_to_dict,
    default_character,
    format_for_prompt,
    format_summary,
)
from src.games.cosmere.lonelog import log_narrative_line, log_roll, narrative_context_for_ai, read_tail
from src.games.cosmere.narrator import synthesize_journal_entry, synthesize_lonelog_summary
from src.games.gm_solo.game_handlers import GmSoloHandlers
from src.games.saves import PlayContext

GAME_ID = "cosmere"

_NARRATOR_SHORTCUTS = frozenset({"skill_test", "combat_attack", "plot_dice"})


def _shortcut_kwargs(ctx: PlayContext) -> dict:
    char = character_from_dict(ctx.entity or {})
    return {
        "plot_dice_pool": char.plot_dice_pool,
        "path": char.path,
        "role": char.role,
        "expertises": list(char.expertises),
        "deflection": char.deflection,
    }


def _apply_shortcut_state(ctx: PlayContext, run: dict, entity: CosmereCharacter) -> None:
    summary = str(run.get("user_message", ""))[:200]
    entity.last_roll_summary = summary
    dice = run.get("dice")
    if isinstance(dice, dict) and "summary" in dice:
        entity.last_roll_summary = str(dice["summary"])[:200]


def _synthesize(mechanics: str, *, entity: CosmereCharacter, chat_provider) -> str | None:
    story_so_far = narrative_context_for_ai(entity.id) if entity.id else ""
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


HANDLERS = GmSoloHandlers(
    game_id=GAME_ID,
    entity_from_dict=character_from_dict,
    entity_to_dict=character_to_dict,
    default_entity=default_character,
    format_summary=format_summary,
    format_for_prompt=format_for_prompt,
    shortcuts=SHORTCUTS,
    shortcut_ids=SHORTCUT_IDS,
    match_shortcut=match_cosmere_shortcut,
    run_shortcut=run_shortcut,
    shortcut_kwargs=_shortcut_kwargs,
    apply_shortcut_state=_apply_shortcut_state,
    narrator_shortcuts=_NARRATOR_SHORTCUTS,
    synthesize_journal=_synthesize,
    log_draw=_log_draw,
    read_lonelog_tail=read_tail,
    character_options=character_options_payload,
    gm_role="Game Master",
)

character_header = HANDLERS.character_header
persist_character = HANDLERS.persist_character
reset_character = HANDLERS.reset_character
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
