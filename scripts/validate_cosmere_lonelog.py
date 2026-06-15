#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.cosmere.entity import CosmereCharacter, character_from_dict, character_to_dict, format_summary


def main() -> int:
    char = CosmereCharacter(
        name="Kaladin",
        path="warrior",
        role="leader",
        expertises=["Athletics", "Leadership"],
        plot_dice_pool=2,
        deflection=3,
    )
    char.clamp()
    assert char.plot_dice_pool == 2
    data = character_to_dict(char)
    restored = character_from_dict(data)
    assert restored.name == "Kaladin"
    assert restored.expertises == ["Athletics", "Leadership"]
    summary = format_summary(restored)
    assert "Kaladin" in summary
    assert "2" in summary
    print("validate_cosmere_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
