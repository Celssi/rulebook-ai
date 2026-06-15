#!/usr/bin/env python3
"""Validate D&D 5e character creation curated data."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.dnd5e.character_builder import level_up, rebuild_character, spell_limits, compute_spell_slots
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
        "sorcerer": {"mode": "known", "cantrips": 4, "picks": 2, "slots": {"1": 2}},
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

    print("validate_dnd5e_character: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
