"""System prompts and language handling (English-only)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.games.registry import (
    DEFAULT_GAME_ID,
    GAME_APOTHECARIA,
    GAME_ASHES,
    GAME_BRAMBLETREK,
    GAME_BRAMBLETREK_2,
    GAME_COLOSTLE,
    GAME_LIGHTHOUSE,
    GAME_SANSIBILIA,
    GAME_WHISPERS,
)

if TYPE_CHECKING:
    from src.games.brambletrek.character import BrambletrekCharacter
    from src.games.warhammer_40k.state import GameState


def detect_language(question: str) -> str:
    """Return language code. Project is English-only."""
    _ = question
    return "en"


def build_system_prompt(
    language: str,
    game: "GameState | None" = None,
    game_id: str = DEFAULT_GAME_ID,
    play_entity: dict | None = None,
    story_mode: str = "player",
    card_source: str = "virtual",
) -> str:
    from src.games.warhammer_40k.state import format_for_prompt

    _ = language
    lang_instruction = "Answer in English."

    from src.games.gm_solo.prompt_dispatch import gm_solo_system_prompt

    gm_prompt = gm_solo_system_prompt(
        game_id,
        play_entity=play_entity,
        story_mode=story_mode,
        card_source=card_source,
        language_instruction=lang_instruction,
    )
    if gm_prompt:
        return gm_prompt

    if game_id == GAME_BRAMBLETREK:
        from src.games.brambletrek.character import character_from_dict
        from src.games.brambletrek.prompts import brambletrek_system_prompt

        return brambletrek_system_prompt(
            language_instruction=lang_instruction,
            character=character_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
        )

    if game_id == GAME_BRAMBLETREK_2:
        from src.games.brambletrek_2.character import character_from_dict as bt2_from_dict
        from src.games.brambletrek_2.prompts import brambletrek_2_system_prompt

        return brambletrek_2_system_prompt(
            language_instruction=lang_instruction,
            character=bt2_from_dict(play_entity) if play_entity else None,
            story_mode=story_mode,
            card_source=card_source,
        )

    if game_id == GAME_SANSIBILIA:
        from src.games.sansibilia.visit import format_for_prompt as format_visit
        from src.games.sansibilia.visit import visit_from_dict

        visit = visit_from_dict(play_entity) if play_entity else None
        visit_block = format_visit(visit, card_source=card_source, story_mode=story_mode)
        visit_section = f"\n\n{visit_block}" if visit_block else ""
        story_rules = (
            "- In **player** story mode: show card-oracle results only. Do not write journal prose "
            "unless the user asks.\n"
            "- In **ai_narrator** story mode: after a day draw, write evocative first-person journal "
            "prose inspired by the adjective + location/event prompt.\n"
            if story_mode == "ai_narrator"
            else "- In **player** story mode: facilitate rules and card lookups; the player writes "
            "their own journal entries.\n"
        )
        card_rules = (
            "- **Physical deck** mode: do not auto-draw cards. The user reports physical pulls.\n"
            if card_source == "physical"
            else "- **Virtual deck** mode: tool draws are authoritative.\n"
        )
        return f"""You are a San Sibilia solo journaling assistant for personal play.

{lang_instruction}
{visit_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say so clearly.
- San Sibilia uses a 52-card deck (no jokers): character table, adjective table (red vs black suits), location/event table, and city-change prompts.
- When tool output includes drawn cards, state them clearly then explain table meanings from context.
- Do not invent journal outcomes in player story mode; in ai_narrator mode, journal prose is welcome when drawing the day's cards.
{story_rules}{card_rules}- Keep answers concise and practical for solo journaling.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (@ action, d: draw).
"""

    if game_id == GAME_LIGHTHOUSE:
        from src.games.lighthouse.watch import format_for_prompt as format_watch
        from src.games.lighthouse.watch import watch_from_dict

        watch = watch_from_dict(play_entity) if play_entity else None
        watch_block = format_watch(watch, card_source=card_source, story_mode=story_mode)
        watch_section = f"\n\n{watch_block}" if watch_block else ""
        story_rules = (
            "- In **player** story mode: show mechanical results only; the keeper writes the logbook.\n"
            "- In **ai_narrator** story mode: write evocative first-person logbook prose after tasks.\n"
            if story_mode == "ai_narrator"
            else "- In **player** story mode: facilitate rules and card lookups; the player journals.\n"
        )
        card_rules = (
            "- **Physical deck** mode: do not auto-draw cards.\n"
            if card_source == "physical"
            else "- **Virtual deck** mode: tool draws are authoritative.\n"
        )
        return f"""You are a Lighthouse keeper solo journaling assistant.

{lang_instruction}
{watch_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say so clearly.
- The game uses a 52-card deck, a d6, and a coin. Tasks: light the lamp, maintenance, observation, events, beachcombing.
- When tool output includes draws or rolls, state them clearly then explain meanings from context.
{story_rules}{card_rules}- Keep answers meditative and practical for solo play at the edge of the universe.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (d: draw, => narrative).
"""

    if game_id == GAME_APOTHECARIA:
        from src.games.apothecaria.cottage import cottage_from_dict, format_for_prompt as format_cottage

        cottage = cottage_from_dict(play_entity) if play_entity else None
        cottage_block = format_cottage(cottage, card_source=card_source, story_mode=story_mode)
        cottage_section = f"\n\n{cottage_block}" if cottage_block else ""
        story_rules = (
            "- In **player** story mode: show card-oracle and foraging results only.\n"
            "- In **ai_narrator** story mode: write journal prose after diagnoses and foraging.\n"
            if story_mode == "ai_narrator"
            else "- In **player** story mode: facilitate rules and table lookups; the player journals.\n"
        )
        card_rules = (
            "- **Physical deck** mode: do not auto-draw cards.\n"
            if card_source == "physical"
            else "- **Virtual deck** mode: tool draws are authoritative.\n"
        )
        return f"""You are an Apothecaria solo journaling assistant for village witch play in High Rannoc.

{lang_instruction}
{cottage_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say so clearly.
- Apothecaria uses ailments (by card rank and reputation tier), reagents with [TAGS], locales, and foraging.
- Patient types: hearts=Villager, diamonds=Adventurer, clubs=Monster, spades=Repeat patient.
- When tool output includes drawn cards, state them clearly then explain table meanings from context.
{story_rules}{card_rules}- Keep answers practical for solo potion-making play.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (@ action, d: draw, => narrative).
"""

    if game_id == GAME_WHISPERS:
        from src.games.whispers.investigation import format_for_prompt as format_investigation
        from src.games.whispers.investigation import investigation_from_dict

        inv = investigation_from_dict(play_entity) if play_entity else None
        inv_block = format_investigation(inv, card_source=card_source, story_mode=story_mode)
        inv_section = f"\n\n{inv_block}" if inv_block else ""
        story_rules = (
            "- In **player** story mode: show card-oracle results only. Do not write journal prose "
            "unless the user asks.\n"
            "- In **ai_narrator** story mode: after a whisper draw, write evocative first-person "
            "horror journal prose inspired by the prompt.\n"
            if story_mode == "ai_narrator"
            else "- In **player** story mode: facilitate rules and card lookups; the player writes "
            "their own investigation journal.\n"
        )
        card_rules = (
            "- **Physical deck** mode: user reports pulls from their constructed Whispers deck.\n"
            if card_source == "physical"
            else "- **Virtual deck** mode: app builds and draws from the Whispers deck.\n"
        )
        return f"""You are a Whispers in the Walls solo horror journaling assistant.

{lang_instruction}
{inv_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say so clearly.
- Whispers uses a constructed Whispers deck (jokers + spades hollows, hearts/diamonds/clubs secrets).
- Suit tables: hearts=walls, diamonds=floors, clubs=overhead, spades=hollows. Location from first draw.
- When tool output includes drawn cards, state them clearly then explain table meanings from context.
{story_rules}{card_rules}- Keep answers concise and practical for solo horror journaling.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (@ action, d: draw, => narrative).
"""

    if game_id == GAME_COLOSTLE:
        from src.games.colostle.character import character_from_dict, format_for_prompt as format_character

        char = character_from_dict(play_entity) if play_entity else None
        char_block = format_character(char, card_source=card_source, story_mode=story_mode)
        char_section = f"\n\n{char_block}" if char_block else ""
        story_rules = (
            "- In **player** story mode: show exploration/combat card results only.\n"
            "- In **ai_narrator** story mode: write first-person journal prose after exploration draws.\n"
            if story_mode == "ai_narrator"
            else "- In **player** story mode: facilitate rules and table lookups; the player journals.\n"
        )
        card_rules = (
            "- **Physical deck** mode: do not auto-draw cards.\n"
            if card_source == "physical"
            else "- **Virtual deck** mode: tool draws are authoritative.\n"
        )
        return f"""You are a Colostle solo RPG adventure assistant.

{lang_instruction}
{char_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say so clearly.
- Colostle uses a 52-card deck for exploration (draw equal to exploration score), combat, oracles, and NPCs.
- Red cards = organic encounters; black cards = structures and scenery. J/Q/K may trigger items or Rooks.
- Classes set exploration and combat scores (Armed 3/4, Followed 5/3, Helmed 2/5, Mounted 5/2).
- When tool output includes drawn cards, state them clearly then explain table meanings from context.
{story_rules}{card_rules}- Keep answers mythic and practical for solo journaling in the Roomlands.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (@ action, d: draw, => narrative).
"""

    if game_id == GAME_ASHES:
        from src.games.ashes.scion import format_for_prompt as format_scion
        from src.games.ashes.scion import scion_from_dict

        scion = scion_from_dict(play_entity) if play_entity else None
        scion_block = format_scion(scion, card_source=card_source, story_mode=story_mode)
        scion_section = f"\n\n{scion_block}" if scion_block else ""
        story_rules = (
            "- In **player** story mode: show room draws, journal prompts, and rolls only.\n"
            "- In **ai_narrator** story mode: write evocative journal prose after room/journal draws.\n"
            if story_mode == "ai_narrator"
            else "- In **player** story mode: facilitate rules and card lookups; the player journals.\n"
        )
        card_rules = (
            "- **Physical deck** mode: do not auto-draw cards.\n"
            if card_source == "physical"
            else "- **Virtual deck** mode: tool draws are authoritative.\n"
        )
        return f"""You are an Ashes solo dungeon-crawling assistant for Mayfalls.

{lang_instruction}
{scion_section}

Rules:
- Answer ONLY using the provided context excerpts. If context is insufficient, say so clearly.
- Ashes uses a 52-card deck for rooms and journal prompts, 3d6 checks (target 18 minus stat), and d6 navigation/sanctuary rolls.
- Card rank sets the room; suit sets the secondary journal feature (Hearts/Diamonds/Clubs/Spades).
- When tool output includes drawn cards or dice, state them clearly then explain table meanings from context.
{story_rules}{card_rules}- Keep answers concise and practical for solo dungeon journaling.
- When citing rules, mention source file and page number from metadata.
- Session events may be recorded in Lonelog notation (@ action, d: draw, => narrative).
"""

    game_block = format_for_prompt(game, "en")
    game_section = f"\n\n{game_block}" if game_block else ""
    return f"""You are a Warhammer 40,000 rules assistant for personal study and casual games.

{lang_instruction}
{game_section}

Rules:
- Answer ONLY using the provided context excerpts. If the context does not contain enough information, say clearly that it was not found in the documents (do not guess rules).
- When tool output includes a dice roll or drawn card, present that result as a live table event, then tie rule explanations to the cited excerpts only.
- Do not invent rules, dice results, or cards beyond tool output and retrieved context.
- When citing rules, mention the source file and page number from the context metadata.
- Be concise and practical for players at the table.
"""


def tool_output_instructions(route: str) -> str:
    """Extra synthesis guidance when combining tools with rules."""
    if route in {"dice", "cards"}:
        return (
            "The tool result is authoritative for rolls/cards. "
            "Do not change the numbers or card names."
        )
    if route == "card_rag":
        return (
            "The drawn card in the tool result is authoritative. "
            "Explain its meaning using only the cited rule excerpts; do not invent table rows."
        )
    return ""


def format_context_block(nodes: list) -> str:
    """Format retrieved nodes for the LLM prompt."""
    parts: list[str] = []
    for i, node in enumerate(nodes, 1):
        meta = node.metadata or {}
        source = meta.get("source_label") or meta.get("source_file", "unknown")
        page = meta.get("page", "?")
        faction = meta.get("faction", "")
        header = f"[{i}] {source} (page {page}, faction={faction})"
        parts.append(f"{header}\n{node.get_content()}")
    return "\n\n---\n\n".join(parts)
