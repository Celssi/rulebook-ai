"""The One Ring play handlers (GmSoloHandlers)."""

from __future__ import annotations

from src.games.gm_solo.game_handlers import GmSoloHandlers
from src.games.saves import PlayContext
from src.games.tor.actions import SHORTCUT_IDS, SHORTCUTS, match_tor_shortcut, run_shortcut
from src.games.tor.entity import (
    TorHero,
    character_options_payload,
    default_hero,
    format_for_prompt,
    format_summary,
    hero_from_dict,
    hero_to_dict,
)
from src.games.tor.lonelog import log_narrative_line, log_roll, narrative_context_for_ai, read_tail
from src.games.tor.narrator import synthesize_journal_entry, synthesize_lonelog_summary

GAME_ID = "tor"

_NARRATOR_SHORTCUTS = frozenset({"tor_skill", "journey_event", "lore_draw", "patron_quest"})


def _shortcut_kwargs(ctx: PlayContext) -> dict:
    hero = hero_from_dict(ctx.entity or {})
    return {
        "name": hero.name,
        "culture": hero.culture,
        "calling": hero.calling,
        "patron": hero.patron,
        "hope": hero.hope,
        "dread": hero.dread,
        "weary": hero.weary,
        "eye_awareness": hero.eye_awareness,
        "safe_haven": hero.safe_haven,
        "journey_day": hero.journey_day,
        "hunt_region": hero.hunt_region,
        "strider": hero.strider,
    }


def _apply_shortcut_state(ctx: PlayContext, run: dict, entity: TorHero) -> None:
    patch = run.get("entity_patch")
    if isinstance(patch, dict):
        delta = patch.get("eye_awareness_delta")
        if delta is not None:
            entity.eye_awareness = max(0, min(20, entity.eye_awareness + int(delta)))
    dice = run.get("dice")
    if isinstance(dice, dict) and dice.get("summary"):
        entity.last_roll_summary = str(dice["summary"])[:200]
    elif run.get("fortune") and isinstance(run["fortune"], dict):
        entity.last_roll_summary = str(run["fortune"].get("summary", ""))[:200]
    elif run.get("journey") and isinstance(run["journey"], dict):
        entity.last_roll_summary = str(run["journey"].get("summary", ""))[:200]
    else:
        entity.last_roll_summary = str(run.get("user_message", ""))[:200]


def _synthesize(mechanics: str, *, entity: TorHero, chat_provider) -> str | None:
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
    entity_from_dict=hero_from_dict,
    entity_to_dict=hero_to_dict,
    default_entity=default_hero,
    format_summary=format_summary,
    format_for_prompt=format_for_prompt,
    shortcuts=SHORTCUTS,
    shortcut_ids=SHORTCUT_IDS,
    match_shortcut=match_tor_shortcut,
    run_shortcut=run_shortcut,
    shortcut_kwargs=_shortcut_kwargs,
    apply_shortcut_state=_apply_shortcut_state,
    narrator_shortcuts=_NARRATOR_SHORTCUTS,
    synthesize_journal=_synthesize,
    log_draw=_log_draw,
    read_lonelog_tail=read_tail,
    character_options=character_options_payload,
    gm_role="Loremaster",
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
