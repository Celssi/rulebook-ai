#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.coriolis.character import (
    CoriolisExplorer,
    crew_from_dict,
    crew_to_dict,
    format_summary,
)


def main() -> int:
    explorer = CoriolisExplorer(
        name="Layla",
        profession="traveler",
        specialty="tugship_pilot",
        crew_name="The Orpheus Run",
        bird_name="Far Horizon",
        shuttle_name="Dust Lark",
        attributes={
            "strength": 3,
            "agility": 4,
            "logic": 4,
            "perception": 5,
            "insight": 4,
            "empathy": 4,
        },
        talents={"shuttle_pilot": 2, "lookout": 1},
        gear_bonus=2,
    )
    explorer.clamp()
    data = crew_to_dict(explorer)
    restored = crew_from_dict(data)
    assert restored.name == "Layla"
    assert restored.crew_name == "The Orpheus Run"
    assert restored.bird_name == "Far Horizon"
    assert restored.roll_pool("perception", "shuttle_pilot") >= 7
    assert restored.max_health() == 7
    assert restored.max_hope() == 8
    summary = format_summary(restored)
    assert "Layla" in summary
    assert "Far Horizon" in summary
    print("validate_coriolis_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
