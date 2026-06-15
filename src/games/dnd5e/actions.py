"""D&D 5e shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.dnd5e.character_builder import long_rest_recover, short_rest_heal
from src.games.dnd5e.curated import roll_oracle
from src.games.dnd5e.entity import Dnd5eCharacter, character_from_dict
from src.games.gm_solo.dice import roll_advantage_d20, roll_death_saves
from src.play_tools import roll_dice

GAME_ID = "dnd5e"

ShortcutKind = Literal["roll", "roll_rag", "rag_only", "static"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "ability_check", "label": "Ability check", "kind": "roll_rag"},
    {"id": "saving_throw", "label": "Saving throw", "kind": "roll_rag"},
    {"id": "attack_roll", "label": "Attack roll", "kind": "roll_rag"},
    {"id": "initiative", "label": "Initiative", "kind": "roll"},
    {"id": "death_save", "label": "Death save", "kind": "roll"},
    {"id": "oracle", "label": "Oracle (d6 yes/no)", "kind": "roll"},
    {"id": "short_rest", "label": "Short rest", "kind": "roll_rag"},
    {"id": "long_rest", "label": "Long rest", "kind": "roll_rag"},
    {"id": "rules_help", "label": "D&D 5e rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_dnd5e_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if "ability check" in lower or "skill check" in lower:
        return "ability_check"
    if "saving throw" in lower or "save roll" in lower:
        return "saving_throw"
    if "attack roll" in lower or ("attack" in lower and "dnd" in lower):
        return "attack_roll"
    if "initiative" in lower:
        return "initiative"
    if "death save" in lower:
        return "death_save"
    if "oracle" in lower or ("d6" in lower and ("yes" in lower or "no" in lower)):
        return "oracle"
    if "short rest" in lower:
        return "short_rest"
    if "long rest" in lower:
        return "long_rest"
    if "dnd rules" in lower or "d&d rules" in lower or "how to play dnd" in lower:
        return "rules_help"
    return None


def _resolve_modifier(
    ability: str,
    ability_scores: dict | None,
    modifier: int | None,
    proficient: bool,
    level: int,
) -> int:
    if modifier is not None:
        return int(modifier)
    scores = ability_scores or {}
    score = int(scores.get(ability.lower(), 10) or 10)
    mod = (score - 10) // 2
    if proficient:
        mod += 2 + (max(1, int(level or 1)) - 1) // 4
    return mod


def _char_from_kwargs(**kwargs) -> Dnd5eCharacter:
    return character_from_dict(
        {
            "name": kwargs.get("name", ""),
            "species": kwargs.get("species", ""),
            "class_name": kwargs.get("class_name", ""),
            "level": kwargs.get("level", 1),
            "hp": kwargs.get("hp", 0),
            "max_hp": kwargs.get("max_hp", 0),
            "hit_die": kwargs.get("hit_die", 8),
            "hit_dice_max": kwargs.get("hit_dice_max", kwargs.get("level", 1)),
            "hit_dice_spent": kwargs.get("hit_dice_spent", 0),
            "ability_scores": kwargs.get("ability_scores") or {},
            "spell_slots": kwargs.get("spell_slots") or {},
        }
    )


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_ID,
    name: str = "",
    species: str = "",
    class_name: str = "",
    level: int = 1,
    hp: int = 0,
    max_hp: int = 0,
    ac: int = 10,
    hit_die: int = 8,
    hit_dice_max: int = 0,
    hit_dice_spent: int = 0,
    ability_scores: dict | None = None,
    spell_slots: dict | None = None,
    ability: str = "dex",
    modifier: int | None = None,
    proficient: bool = False,
    advantage: str = "normal",
    target_ac: int | None = None,
    hit_dice_to_spend: int = 1,
    **_kwargs,
) -> dict:
    _ = game_id, ac
    who = name.strip() or "the character"
    build = f"{who}"
    if species or class_name:
        build = f"{who} ({species} {class_name} {level})".strip()

    if shortcut_id == "ability_check":
        mod = _resolve_modifier(ability, ability_scores, modifier, proficient, level)
        adv = advantage if advantage in ("normal", "advantage", "disadvantage") else "normal"
        result = roll_advantage_d20(mod, advantage=adv)  # type: ignore[arg-type]
        prof = " (proficient)" if proficient else ""
        user = f"**Ability check** ({ability.upper()}{prof})\n\n{result['summary']}"
        prompt = (
            f"D&D 5e ability check for {build}, {ability.upper()} modifier {mod:+d}. "
            f"{result['summary']}. Explain DC, success, and any relevant 2024 PHB guidance."
        )
        return {"user_message": user, "prompt": prompt, "dice": result, "task": "ability_check"}

    if shortcut_id == "saving_throw":
        mod = _resolve_modifier(ability, ability_scores, modifier, proficient, level)
        adv = advantage if advantage in ("normal", "advantage", "disadvantage") else "normal"
        result = roll_advantage_d20(mod, advantage=adv)  # type: ignore[arg-type]
        user = f"**Saving throw** ({ability.upper()})\n\n{result['summary']}"
        prompt = (
            f"D&D 5e saving throw for {build}, {ability.upper()} save {mod:+d}. "
            f"{result['summary']}. Explain save DC, success, and effects using PHB rules."
        )
        return {"user_message": user, "prompt": prompt, "dice": result, "task": "saving_throw"}

    if shortcut_id == "attack_roll":
        mod = _resolve_modifier(ability, ability_scores, modifier, proficient, level)
        adv = advantage if advantage in ("normal", "advantage", "disadvantage") else "normal"
        result = roll_advantage_d20(mod, advantage=adv)  # type: ignore[arg-type]
        if target_ac is not None:
            ac_note = f"\n\nvs target AC **{int(target_ac)}**"
            ac_prompt = f" vs AC {int(target_ac)}"
        else:
            ac_note = "\n\n(Set target AC when you know the foe's armor class.)"
            ac_prompt = " vs DM-set AC"
        user = f"**Attack roll**\n\n{result['summary']}{ac_note}"
        prompt = (
            f"D&D 5e attack roll for {build}, attack bonus {mod:+d}{ac_prompt}. "
            f"{result['summary']}. Explain hit, critical hit, and damage next steps."
        )
        return {"user_message": user, "prompt": prompt, "dice": result, "task": "attack_roll"}

    if shortcut_id == "initiative":
        mod = _resolve_modifier("dex", ability_scores, modifier, False, level)
        result = roll_dice(f"1d20{mod:+d}" if mod else "1d20")
        total = int(result.get("total", 0))
        user = f"**Initiative**\n\n{result.get('summary', f'd20+{mod} = {total}')}"
        return {"user_message": user, "prompt": user, "static": True, "dice": result}

    if shortcut_id == "death_save":
        result = roll_death_saves()
        user = f"**Death save** (HP {hp}/{max_hp})\n\n{result['summary']}"
        prompt = (
            f"D&D 5e death saving throw for {build} at {hp}/{max_hp} HP. "
            f"{result['summary']}. Explain death save rules and outcomes."
        )
        return {"user_message": user, "prompt": prompt, "dice": result, "task": "death_save"}

    if shortcut_id == "oracle":
        result = roll_oracle()
        user = f"**Solo oracle (d6)**\n\n{result['summary']}"
        return {"user_message": user, "prompt": user, "static": True, "dice": result, "task": "oracle"}

    if shortcut_id == "short_rest":
        char = _char_from_kwargs(
            name=name,
            species=species,
            class_name=class_name,
            level=level,
            hp=hp,
            max_hp=max_hp,
            hit_die=hit_die,
            hit_dice_max=hit_dice_max or level,
            hit_dice_spent=hit_dice_spent,
            ability_scores=ability_scores,
            spell_slots=spell_slots,
        )
        rest = short_rest_heal(char, dice_to_spend=hit_dice_to_spend)
        user = f"**Short rest**\n\n{rest['summary']}"
        prompt = (
            f"D&D 5e short rest for {build}. {rest['summary']}. "
            "Explain remaining short rest options: more Hit Dice, class features, "
            "and limitations per 2024 PHB."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "dice": {"summary": rest["summary"], "rolls": rest.get("rolls", [])},
            "entity_updates": rest.get("entity_updates") or {},
            "task": "short_rest",
        }

    if shortcut_id == "long_rest":
        char = _char_from_kwargs(
            name=name,
            species=species,
            class_name=class_name,
            level=level,
            hp=hp,
            max_hp=max_hp,
            hit_die=hit_die,
            hit_dice_max=hit_dice_max or level,
            hit_dice_spent=hit_dice_spent,
            ability_scores=ability_scores,
            spell_slots=spell_slots,
        )
        rest = long_rest_recover(char)
        user = f"**Long rest**\n\n{rest['summary']}"
        prompt = (
            f"D&D 5e long rest for {build}. {rest['summary']}. "
            "Explain long rest limits and anything not recovered per 2024 PHB."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "static": False,
            "rag_only": True,
            "entity_updates": rest.get("entity_updates") or {},
            "task": "long_rest",
        }

    if shortcut_id == "rules_help":
        prompt = (
            "Explain how to run D&D 5e solo as player and DM: ability checks, saves, combat, "
            "rests, death saves, and using oracle tables for unknown outcomes. "
            "Reference Player's Handbook and DMG; use Faerûn supplements only when the campaign is set in Faerûn."
        )
        return {"user_message": "**D&D 5e rules**", "prompt": prompt, "rag_only": True}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
