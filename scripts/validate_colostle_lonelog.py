#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.colostle.character import ColostleCharacter, character_from_dict, character_to_dict, format_summary


def main() -> int:
    char = ColostleCharacter(name="Test", character_class="armed", exploration_score=3, combat_score=4)
    char.clamp()
    assert char.exploration_score == 3
    data = character_to_dict(char)
    restored = character_from_dict(data)
    assert restored.name == "Test"
    summary = format_summary(restored)
    assert "Test" in summary
    assert "3" in summary
    print("validate_colostle_lonelog: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
