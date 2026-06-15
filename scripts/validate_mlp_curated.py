#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.mlp.actions import run_shortcut
from src.games.mlp.curated import validate_level1_character
from src.games.mlp.dice import roll_skill_test
from src.games.mlp.entity import default_pony, pony_from_dict, pony_to_dict


def main() -> int:
    test = roll_skill_test(3, 15, skill_name="Alertness")
    assert test["ok"]
    assert "DIF" in test["summary"]

    shift = run_shortcut(
        "pay_spell_cost",
        pony_name="Twilight",
        spellcasting_rank=3,
        spellcasting_current=7,
        spell_cost=1,
    )
    assert "downshift" in shift["user_message"].lower()
    assert "new_spellcasting_current" in shift

    recover = run_shortcut(
        "recover_spellcasting",
        pony_name="Twilight",
        spellcasting_rank=3,
        spellcasting_current=8,
    )
    assert "Recover spellcasting" in recover["user_message"]
    assert recover.get("new_spellcasting_current") is not None

    skill = run_shortcut(
        "skill_test",
        pony_name="Rainbow",
        origin="pegasus",
        skills={"acrobatics": 4},
        default_skill_id="acrobatics",
        default_dif=15,
    )
    assert "Skill Test" in skill["user_message"]
    assert skill.get("dice")

    pony = default_pony()
    pony.origin = "unicorn"
    pony.role = "spirit_of_magic"
    pony.influences = ["bookworm"]
    pony.base_essences = {"strength": 3, "speed": 3, "smarts": 3, "social": 3}
    pony.clamp()
    errors = validate_level1_character(pony_to_dict(pony))
    assert errors == [], f"expected valid pony, got {errors}"

    legacy = pony_from_dict(
        {
            "pony_type": "pegasus",
            "quirk": "Loves clouds",
            "talent": "Fast flyer",
            "magic_shift": 2,
        }
    )
    assert legacy.origin == "pegasus"
    assert legacy.background_bonds == ["Loves clouds"]
    assert legacy.cutie_mark == "Fast flyer"

    print("validate_mlp_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
