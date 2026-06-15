"""Coriolis play handlers (GmSoloHandlers)."""

from __future__ import annotations

from src.games.coriolis.actions import (
    SHORTCUTS,
    SHORTCUT_IDS,
    match_coriolis_shortcut,
    run_shortcut,
)
from src.games.coriolis.character import (
    CoriolisExplorer,
    character_options_payload,
    crew_from_dict,
    crew_to_dict,
    default_crew,
    format_for_prompt,
    format_summary,
)
from src.games.coriolis.lonelog import log_roll, read_tail
from src.games.coriolis.narrator import synthesize_journal_entry
from src.games.gm_solo.game_handlers import GmSoloHandlers
from src.games.saves import PlayContext

GAME_ID = "coriolis"

_NARRATOR_SHORTCUTS = frozenset({"attribute_roll", "push_roll", "encounter"})
_DEFAULT_ATTRIBUTE = "perception"


def _shortcut_kwargs(ctx: PlayContext) -> dict:
    explorer = crew_from_dict(ctx.entity or {})
    attribute = explorer.last_attribute or _DEFAULT_ATTRIBUTE
    if attribute not in explorer.attributes:
        attribute = _DEFAULT_ATTRIBUTE
    talent = explorer.last_talent or ""
    if talent and talent not in explorer.talents:
        ranked = sorted(explorer.talents.items(), key=lambda x: -x[1])
        talent = ranked[0][0] if ranked and ranked[0][1] > 0 else ""
    base_pool = explorer.roll_pool(attribute, talent)
    return {
        "attribute": attribute,
        "talent": talent,
        "base_pool": base_pool,
        "gear_pool": explorer.gear_bonus,
        "hope": explorer.hope,
        "max_hope": explorer.max_hope(),
        "potential_despair": 1,
        "crew_name": explorer.crew_name or explorer.name,
        "bird_name": explorer.bird_name,
        "shuttle_name": explorer.shuttle_name,
    }


def _apply_shortcut_state(ctx: PlayContext, run: dict, explorer: CoriolisExplorer) -> None:
    if run.get("roll_summary"):
        explorer.last_roll_summary = str(run["roll_summary"])
    if "hope" in run:
        explorer.hope = int(run["hope"])
    if "gear_bonus" in run:
        explorer.gear_bonus = int(run["gear_bonus"])
    attribute = run.get("attribute")
    if attribute:
        explorer.last_attribute = str(attribute)
    talent = run.get("talent")
    if talent is not None:
        explorer.last_talent = str(talent or "")


def _character_options() -> dict:
    return character_options_payload()


def _log_draw(slot_id: str, label: str, cards: list[str] | None = None) -> None:
    _ = cards
    log_roll(slot_id, label)


HANDLERS = GmSoloHandlers(
    game_id=GAME_ID,
    entity_from_dict=crew_from_dict,
    entity_to_dict=crew_to_dict,
    default_entity=default_crew,
    format_summary=format_summary,
    format_for_prompt=format_for_prompt,
    shortcuts=SHORTCUTS,
    shortcut_ids=SHORTCUT_IDS,
    match_shortcut=match_coriolis_shortcut,
    run_shortcut=run_shortcut,
    shortcut_kwargs=_shortcut_kwargs,
    apply_shortcut_state=_apply_shortcut_state,
    narrator_shortcuts=_NARRATOR_SHORTCUTS,
    synthesize_journal=synthesize_journal_entry,
    log_draw=_log_draw,
    read_lonelog_tail=read_tail,
    character_options=_character_options,
    gm_role="Game Master",
)

character_header = HANDLERS.character_header
persist_character = HANDLERS.persist_character
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
