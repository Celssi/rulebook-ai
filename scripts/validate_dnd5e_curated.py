#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.dnd5e.curated import all_oracle_faces_valid, lookup_oracle, roll_oracle
from src.games.gm_solo.dice import roll_advantage_d20, roll_death_saves


def main() -> int:
    assert all_oracle_faces_valid()
    yes = lookup_oracle(5)
    assert yes["answer"] == "Yes"
    no = lookup_oracle(2)
    assert no["answer"] == "No"
    oracle = roll_oracle()
    assert 1 <= oracle["roll"] <= 6

    adv = roll_advantage_d20(3, advantage="advantage")
    assert adv["total"] == adv["chosen"] + 3

    death = roll_death_saves()
    assert death["roll"] in range(1, 21)
    assert death["outcome"]

    print("validate_dnd5e_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
