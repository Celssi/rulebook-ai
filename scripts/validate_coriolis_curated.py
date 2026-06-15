#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.coriolis.curated import (
    all_encounters_valid,
    all_professions_valid,
    all_trauma_valid,
    roll_despair_resist,
    roll_encounter,
    roll_mental_trauma,
)


def main() -> int:
    assert all_professions_valid()
    assert all_encounters_valid()
    assert all_trauma_valid()
    enc = roll_encounter()
    assert enc.get("text")
    despair = roll_despair_resist(empathy=3, potential_despair=2)
    assert despair.get("summary")
    assert "Despair resist" in despair["summary"]
    trauma = roll_mental_trauma()
    assert trauma.get("summary")
    assert "Mental trauma" in trauma["summary"]
    print("validate_coriolis_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
