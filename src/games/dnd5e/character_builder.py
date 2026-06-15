"""Apply PHB 2024 rules when building or leveling a D&D 5e character."""

from __future__ import annotations

import random
from typing import Any

from src.games.dnd5e.character_data import (
    full_caster_slots,
    get_armor,
    get_background,
    get_class,
    get_species,
    half_caster_slots,
    shield_ac_bonus,
    skills_data,
)
from src.games.dnd5e.entity import ABILITY_KEYS, Dnd5eCharacter

_SPELLCASTING_FULL = {"bard", "cleric", "druid", "sorcerer", "wizard"}
_SPELLCASTING_HALF = {"paladin", "ranger"}
_SPELLCASTING_PACT = {"warlock"}


def _level_index(level: int) -> int:
    return max(0, min(19, int(level or 1) - 1))


def _by_level(table: list | None, level: int, default: int = 0) -> int:
    if not isinstance(table, list) or not table:
        return default
    return int(table[_level_index(level)] or default)


def apply_background_asi(
    scores: dict[str, int],
    background_id: str,
    *,
    plus2: str = "",
    plus1: str = "",
    all_three: bool = False,
) -> dict[str, int]:
    """Background ASI: +2/+1 to two of three abilities, or +1 to all three."""
    bg = get_background(background_id)
    if not bg:
        return dict(scores)
    out = dict(scores)
    options = [str(a).lower() for a in (bg.get("ability_scores") or []) if str(a).lower() in ABILITY_KEYS]
    if not options:
        return out
    if all_three:
        for ab in options[:3]:
            out[ab] = min(20, out.get(ab, 8) + 1)
        return out
    p2 = plus2.lower() if plus2.lower() in options else options[0]
    remaining = [a for a in options if a != p2]
    p1 = plus1.lower() if plus1.lower() in remaining else (remaining[0] if remaining else p2)
    out[p2] = min(20, out.get(p2, 8) + 2)
    out[p1] = min(20, out.get(p1, 8) + 1)
    return out


def standard_array_for_class(class_id: str) -> dict[str, int]:
    table = skills_data().get("standard_array_by_class") or {}
    row = table.get(class_id)
    if isinstance(row, dict):
        return {k: int(row.get(k, 10) or 10) for k in ABILITY_KEYS}
    return {k: 10 for k in ABILITY_KEYS}


def compute_spell_slots(char: Dnd5eCharacter) -> dict[str, int]:
    cls = get_class(char.class_name)
    if not cls or not cls.get("spellcasting"):
        return {}
    cid = char.class_name
    level = char.level
    mode = cls.get("spellcasting")
    if mode == "pact":
        pact = cls.get("pact_slots_by_level") or []
        row = pact[_level_index(level)] if pact else {}
        if isinstance(row, dict):
            count = int(row.get("slots", 0) or 0)
            slot_level = int(row.get("level", 1) or 1)
            if count > 0:
                return {str(slot_level): count}
        return {}
    if cid in _SPELLCASTING_HALF or mode == "prepared" and cid in _SPELLCASTING_HALF:
        return half_caster_slots(level)
    if cid in _SPELLCASTING_FULL or mode in ("prepared", "known"):
        return full_caster_slots(level)
    return {}


def compute_max_hp(char: Dnd5eCharacter, *, first_level: bool = False) -> int:
    cls = get_class(char.class_name)
    hit_die = int((cls or {}).get("hit_die", 8) or 8)
    con_mod = char.ability_modifier("con")
    if char.level <= 1:
        return max(1, hit_die + con_mod)
    # Level 1 + (level-1) * (avg hit die + con mod); use rolled average (hit_die//2 + 1)
    per_level = max(1, (hit_die // 2) + 1 + con_mod)
    return max(1, hit_die + con_mod + per_level * (char.level - 1))


def merge_proficiencies(char: Dnd5eCharacter) -> tuple[list[str], list[str], list[str]]:
    """Return (skills, saves, tools) after class + background."""
    cls = get_class(char.class_name)
    bg = get_background(char.background)
    saves = list((cls or {}).get("saving_throws") or [])
    skills = list(char.skill_proficiencies or [])
    tools = list(char.tool_proficiencies or [])
    if bg:
        for sk in bg.get("skills") or []:
            s = str(sk).lower()
            if s and s not in skills:
                skills.append(s)
        tool = str(bg.get("tool") or "").strip()
        if tool and tool not in tools:
            tools.append(tool)
    for sk in char.class_skill_choices or []:
        s = str(sk).lower()
        if s and s not in skills:
            skills.append(s)
    if char.species == "human" and char.human_skill:
        hs = str(char.human_skill).lower()
        if hs and hs not in skills:
            skills.append(hs)
    return skills, [str(s).lower() for s in saves], tools


def spell_limits(char: Dnd5eCharacter) -> dict[str, int]:
    cls = get_class(char.class_name)
    if not cls or not cls.get("spellcasting"):
        return {"cantrips": 0, "prepared": 0, "known": 0}
    level = char.level
    cantrips = _by_level(cls.get("cantrips_by_level"), level, 0)
    prepared = _by_level(cls.get("prepared_by_level"), level, 0)
    known = _by_level(cls.get("spells_known_by_level"), level, 0)
    return {"cantrips": cantrips, "prepared": prepared, "known": known}


def rebuild_character(char: Dnd5eCharacter, *, recompute_hp: bool = False) -> Dnd5eCharacter:
    """Recompute derived stats from class, species, background, and level."""
    char.clamp()
    # Resolve the *base* (pre-background) ability scores, then derive the final
    # scores by applying the background increase exactly once. Tracking the base
    # separately keeps rebuild idempotent — without it, repeated saves would stack
    # the +2/+1 onto already-boosted scores.
    if char.class_name and not char.ability_scores_set:
        base = standard_array_for_class(char.class_name)
    elif char.base_ability_scores:
        base = {
            k: int(char.base_ability_scores.get(k, char.ability_scores.get(k, 10)) or 10)
            for k in ABILITY_KEYS
        }
    else:
        base = {k: int(char.ability_scores.get(k, 10) or 10) for k in ABILITY_KEYS}
    char.base_ability_scores = dict(base)

    final = dict(base)
    if char.background and char.background_asi_mode != "manual":
        final = apply_background_asi(
            final,
            char.background,
            plus2=char.background_asi_plus2,
            plus1=char.background_asi_plus1,
            all_three=char.background_asi_all_three,
        )
    # Apply ability score improvements taken at level-up (idempotent: summed from
    # the recorded choices, not the already-derived scores). Derive feats too.
    feat_names: list[str] = []
    for choice in char.asi_choices:
        if not isinstance(choice, dict):
            continue
        if choice.get("type") == "feat":
            name = str(choice.get("feat") or "").strip()
            if name:
                feat_names.append(name)
        else:
            for ab, amount in (choice.get("plus") or {}).items():
                if ab in ABILITY_KEYS:
                    final[ab] = min(20, final.get(ab, 10) + int(amount or 0))
    char.feats = feat_names
    char.ability_scores = final

    sp = get_species(char.species)
    if sp:
        char.speed = int(sp.get("speed", char.speed) or char.speed)
        sizes = sp.get("size_options") or ["medium"]
        if char.size not in sizes:
            char.size = str(sizes[0])
        if char.species == "human":
            char.heroic_inspiration = True  # Resourceful: gain on long rest

    skills, saves, tools = merge_proficiencies(char)
    char.skill_proficiencies = skills
    char.save_proficiencies = saves
    char.tool_proficiencies = tools

    cls = get_class(char.class_name)
    if cls:
        char.hit_die = int(cls.get("hit_die", char.hit_die) or char.hit_die)
        char.hit_dice_max = char.level
        if char.hit_dice_spent > char.hit_dice_max:
            char.hit_dice_spent = char.hit_dice_max

    char.spell_slots = compute_spell_slots(char)

    if char.class_name:
        bg = get_background(char.background)
        if bg and not char.origin_feat:
            char.origin_feat = str(bg.get("feat") or "")

    if recompute_hp or char.max_hp <= 0:
        new_max = compute_max_hp(char)
        char.max_hp = new_max
        if char.hp <= 0 or char.hp > char.max_hp:
            char.hp = char.max_hp

    # Armor Class from worn armor + shield, unless the player set it manually.
    if not char.ac_manual:
        char.ac = compute_ac(char)
    elif char.ac <= 0:
        char.ac = 10 + char.ability_modifier("dex")

    char.clamp()
    return char


def compute_ac(char: Dnd5eCharacter) -> int:
    """AC from worn armor + shield (PHB 2024 armor table)."""
    dex = char.ability_modifier("dex")
    armor = get_armor(char.armor) if char.armor and char.armor != "none" else None
    if not armor:
        base = 10 + dex
    else:
        base = int(armor.get("base_ac", 10) or 10)
        category = str(armor.get("category", "") or "")
        if armor.get("add_dex") or category == "light":
            base += dex
        elif "dex_cap" in armor or category == "medium":
            base += min(dex, int(armor.get("dex_cap", 2) or 2))
        # heavy armor adds no DEX
    if char.shield:
        base += shield_ac_bonus()
    return max(1, min(30, base))


def level_up(char: Dnd5eCharacter, *, hp_roll: int | None = None) -> Dnd5eCharacter:
    if char.level >= 20:
        return char
    char.level += 1
    cls = get_class(char.class_name)
    hit_die = int((cls or {}).get("hit_die", 8) or 8)
    con_mod = char.ability_modifier("con")
    if hp_roll is None:
        hp_roll = random.randint(1, hit_die)
    gain = max(1, int(hp_roll) + con_mod)
    char.max_hp = max(1, char.max_hp + gain)
    char.hp = min(char.max_hp, char.hp + gain)
    return rebuild_character(char, recompute_hp=False)


# Levels that grant an Ability Score Improvement / feat. Most classes use the
# default; Fighter and Rogue get extras (PHB 2024).
_ASI_LEVELS_DEFAULT = (4, 8, 12, 16, 19)
_ASI_LEVELS_BY_CLASS = {
    "fighter": (4, 6, 8, 12, 14, 16, 19),
    "rogue": (4, 8, 10, 12, 16, 19),
}


def asi_feat_slots(class_id: str, level: int) -> int:
    """Number of ASI/feat choices unlocked by the given level."""
    levels = _ASI_LEVELS_BY_CLASS.get(class_id, _ASI_LEVELS_DEFAULT)
    return sum(1 for lv in levels if level >= lv)


def character_creation_summary(char: Dnd5eCharacter) -> dict[str, Any]:
    limits = spell_limits(char)
    cls = get_class(char.class_name) or {}
    slots = asi_feat_slots(char.class_name, char.level) if char.class_name else 0
    taken = len(char.asi_choices)
    return {
        "proficiency_bonus": char.proficiency_bonus(),
        "spell_limits": limits,
        "spellcasting": cls.get("spellcasting"),
        "subclass_level": cls.get("subclass_level", 3),
        "needs_subclass": char.level >= int(cls.get("subclass_level", 3) or 3) and not char.subclass,
        "hit_die": char.hit_die,
        "hit_dice_available": max(0, char.hit_dice_max - char.hit_dice_spent),
        "asi_feat_slots": slots,
        "asi_feat_taken": taken,
        "needs_asi": slots > taken,
        "ac": char.ac,
    }


def short_rest_heal(
    char: Dnd5eCharacter,
    *,
    dice_to_spend: int = 1,
) -> dict[str, Any]:
    """Spend Hit Dice during a short rest (PHB 2024)."""
    available = max(0, char.hit_dice_max - char.hit_dice_spent)
    spend = min(max(0, int(dice_to_spend)), available)
    if spend <= 0:
        return {
            "healing": 0,
            "rolls": [],
            "dice_spent": 0,
            "summary": "No Hit Dice available to spend.",
            "entity_updates": {},
        }
    con_mod = char.ability_modifier("con")
    rolls: list[int] = []
    total = 0
    for _ in range(spend):
        roll = random.randint(1, char.hit_die)
        healed = max(1, roll + con_mod)
        rolls.append(roll)
        total += healed
    new_hp = min(char.max_hp, char.hp + total)
    return {
        "healing": total,
        "rolls": rolls,
        "dice_spent": spend,
        "summary": (
            f"Short rest: spent {spend}d{char.hit_die} {rolls} + {con_mod:+d} CON "
            f"→ **{total}** HP restored ({char.hp} → {new_hp})"
        ),
        "entity_updates": {
            "hp": new_hp,
            "hit_dice_spent": char.hit_dice_spent + spend,
        },
    }


def long_rest_recover(char: Dnd5eCharacter) -> dict[str, Any]:
    """Apply long rest recovery (HP, Hit Dice, spell slots)."""
    char.hp = char.max_hp
    char.hit_dice_spent = 0
    char.spell_slots = compute_spell_slots(char)
    char.death_save_successes = 0
    char.death_save_failures = 0
    char.exhaustion = max(0, char.exhaustion - 1)  # PHB 2024: long rest removes 1 level
    char.concentration = ""
    if char.species == "human":
        char.heroic_inspiration = True
    char.clamp()
    slots = ", ".join(f"L{k}×{v}" for k, v in sorted(char.spell_slots.items(), key=lambda x: int(x[0])))
    summary = f"Long rest: HP restored to **{char.hp}/{char.max_hp}**, all Hit Dice available"
    if slots:
        summary += f", spell slots restored ({slots})"
    if char.exhaustion:
        summary += f", exhaustion now level {char.exhaustion}"
    return {
        "summary": summary,
        "entity_updates": {
            "hp": char.hp,
            "hit_dice_spent": 0,
            "spell_slots": dict(char.spell_slots),
            "heroic_inspiration": char.heroic_inspiration,
            "death_save_successes": 0,
            "death_save_failures": 0,
            "exhaustion": char.exhaustion,
            "concentration": "",
        },
    }
