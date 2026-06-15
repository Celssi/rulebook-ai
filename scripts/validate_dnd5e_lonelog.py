#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.dnd5e import play as _dnd5e_play  # noqa: F401
from src.games.dnd5e.entity import Dnd5eCharacter, character_from_dict, character_to_dict, format_summary


def main() -> int:
    char = Dnd5eCharacter(
        name="Elara",
        species="Elf",
        class_name="Wizard",
        background="Sage",
        level=3,
        hp=14,
        max_hp=18,
        ac=13,
        ability_scores={"str": 8, "dex": 14, "con": 12, "int": 16, "wis": 12, "cha": 10},
        spell_slots={"1": 4, "2": 2},
    )
    char.clamp()
    assert char.ability_modifier("int") == 3
    assert char.proficiency_bonus() == 2
    data = character_to_dict(char)
    restored = character_from_dict(data)
    assert restored.spell_slots["1"] == 4
    summary = format_summary(restored)
    assert "Elara" in summary
    assert "Wizard" in summary
    print("validate_dnd5e_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
