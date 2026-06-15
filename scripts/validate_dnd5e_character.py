#!/usr/bin/env python3
"""Validate D&D 5e character creation curated data."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.dnd5e.character_builder import (
    character_creation_summary,
    compute_spell_slots,
    level_up,
    rebuild_character,
    spell_limits,
)
from src.games.dnd5e.character_data import (
    character_options_payload,
    get_background,
    get_class,
    get_species,
    list_backgrounds,
    list_classes,
    list_species,
    spell_list_for,
)
from src.games.dnd5e.entity import Dnd5eCharacter, character_from_dict, character_to_dict


def main() -> int:
    assert len(list_classes()) == 12
    assert len(list_species()) == 10
    assert len(list_backgrounds()) == 16
    assert get_class("wizard")["hit_die"] == 6
    assert get_species("elf")["speed"] == 30
    assert get_background("acolyte")["feat"] == "Magic Initiate (Cleric)"

    # Every spellcasting class: limits + spell list at level 1
    caster_expectations = {
        "bard": {"mode": "prepared", "cantrips": 2, "picks": 4, "slots": {"1": 2}},
        "cleric": {"mode": "prepared", "cantrips": 3, "picks": 4, "slots": {"1": 2}},
        "druid": {"mode": "prepared", "cantrips": 2, "picks": 4, "slots": {"1": 2}},
        "wizard": {"mode": "prepared", "cantrips": 3, "picks": 4, "slots": {"1": 2}},
        "sorcerer": {"mode": "prepared", "cantrips": 4, "picks": 2, "slots": {"1": 2}},
        "warlock": {"mode": "pact", "cantrips": 2, "picks": 2, "slots": {"1": 1}},
        "paladin": {"mode": "prepared", "cantrips": 0, "picks": 2, "slots": {"1": 2}},
        "ranger": {"mode": "prepared", "cantrips": 0, "picks": 2, "slots": {"1": 2}},
    }
    for cid, exp in caster_expectations.items():
        cls = get_class(cid)
        assert cls is not None
        assert cls.get("spellcasting") == exp["mode"], cid
        char = Dnd5eCharacter(class_name=cid, level=1)
        lim = spell_limits(char)
        assert lim["cantrips"] == exp["cantrips"], (cid, lim)
        pick_key = "known" if exp["mode"] in ("known", "pact") else "prepared"
        assert lim[pick_key] == exp["picks"], (cid, lim)
        slots = compute_spell_slots(char)
        assert slots == exp["slots"], (cid, slots)
        sl = spell_list_for(cid)
        if exp["cantrips"]:
            assert len(sl.get("cantrips") or []) >= exp["cantrips"], cid
        assert len(sl.get("1") or []) >= exp["picks"], cid

    for cid in ("barbarian", "fighter", "monk", "rogue"):
        char = Dnd5eCharacter(class_name=cid, level=1)
        assert spell_limits(char) == {"cantrips": 0, "prepared": 0, "known": 0}
        assert compute_spell_slots(char) == {}

    opts = character_options_payload()
    assert "classes" in opts and "spell_lists" in opts
    wizard_spells = spell_list_for("wizard")
    assert "cantrips" in wizard_spells and len(wizard_spells["cantrips"]) >= 10

    char = Dnd5eCharacter(
        name="Test",
        species="human",
        class_name="wizard",
        background="sage",
        level=1,
        class_skill_choices=["arcana", "history"],
        cantrips=["fire bolt", "light"],
        prepared_spells=["magic missile", "shield"],
        ability_scores_set=True,
    )
    char = rebuild_character(char, recompute_hp=True)
    assert char.max_hp >= 1
    assert char.spell_slots.get("1", 0) >= 2
    assert "arcana" in char.skill_proficiencies
    assert char.origin_feat == "Magic Initiate (Wizard)"

    data = character_to_dict(char)
    restored = character_from_dict(data)
    assert restored.name == "Test"

    leveled = level_up(rebuild_character(Dnd5eCharacter(name="X", class_name="fighter", level=1)))
    assert leveled.level == 2

    # Regression: background ability increase must not stack across repeated rebuilds.
    stack = Dnd5eCharacter(
        name="Stack",
        species="human",
        class_name="fighter",
        background="soldier",  # STR/DEX/CON, applies +2/+1
        level=1,
        ability_scores_set=True,
        ability_scores={"str": 15, "dex": 14, "con": 13, "int": 8, "wis": 10, "cha": 12},
    )
    stack = rebuild_character(stack)
    first = dict(stack.ability_scores)
    for _ in range(3):
        stack = rebuild_character(stack)
    assert stack.ability_scores == first, (first, stack.ability_scores)
    assert stack.base_ability_scores["str"] == 15, stack.base_ability_scores
    assert stack.ability_scores["str"] == 17, stack.ability_scores  # 15 + 2 background, once

    # Armor-derived AC (PHB 2024 armor table).
    from src.games.dnd5e.character_builder import compute_ac, asi_feat_slots
    from src.games.dnd5e.actions import run_shortcut

    ac_char = Dnd5eCharacter(
        class_name="fighter", level=1, ability_scores_set=True,
        ability_scores={"str": 16, "dex": 14, "con": 14, "int": 8, "wis": 10, "cha": 12},
        armor="breastplate", shield=True,
    )
    ac_char = rebuild_character(ac_char)
    assert ac_char.ac == 18, ("breastplate+shield", ac_char.ac)  # 14 + min(2,2) + 2
    ac_char.armor, ac_char.shield = "plate", False
    ac_char = rebuild_character(ac_char)
    assert ac_char.ac == 18, ("plate", ac_char.ac)
    ac_char.armor = "leather"
    ac_char = rebuild_character(ac_char)
    assert ac_char.ac == 13, ("leather", ac_char.ac)  # 11 + 2 dex
    ac_char.ac_manual, ac_char.ac = True, 21
    ac_char = rebuild_character(ac_char)
    assert ac_char.ac == 21, ("manual override", ac_char.ac)

    # ASI / feat slots and idempotent application.
    assert asi_feat_slots("fighter", 8) == 3  # 4, 6, 8
    assert asi_feat_slots("rogue", 10) == 3  # 4, 8, 10
    assert asi_feat_slots("wizard", 12) == 3  # 4, 8, 12
    asi_char = Dnd5eCharacter(
        class_name="fighter", level=8, ability_scores_set=True,
        ability_scores={"str": 16, "dex": 12, "con": 14, "int": 8, "wis": 10, "cha": 12},
        asi_choices=[{"type": "asi", "plus": {"str": 2}}, {"type": "feat", "feat": "Sentinel"}],
    )
    asi_char = rebuild_character(asi_char)
    assert asi_char.ability_scores["str"] == 18, asi_char.ability_scores
    assert asi_char.feats == ["sentinel"], asi_char.feats
    before = asi_char.ability_scores["str"]
    for _ in range(3):
        asi_char = rebuild_character(asi_char)
    assert asi_char.ability_scores["str"] == before
    summ = character_creation_summary(asi_char)
    assert summ["asi_feat_slots"] == 3 and summ["needs_asi"] is True

    # Death save shortcut tracks running tally and persists via entity_updates.
    run = run_shortcut("death_save", hp=0, max_hp=12, death_save_successes=2, death_save_failures=0)
    upd = run["entity_updates"]
    assert "death_save_successes" in upd and "death_save_failures" in upd

    print("validate_dnd5e_character: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
