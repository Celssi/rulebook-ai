#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.outgunned.character import (
    OutgunnedHero,
    format_summary,
    hero_from_dict,
    hero_to_dict,
)


def main() -> int:
    hero = OutgunnedHero(name="McClane", mission_title="Stop the heist", ad_state={"phase": "Pressure"})
    hero.clamp()
    data = hero_to_dict(hero)
    restored = hero_from_dict(data)
    assert restored.name == "McClane"
    assert restored.mission_title == "Stop the heist"
    assert restored.ad_state.get("phase") == "Pressure"
    summary = format_summary(restored)
    assert "McClane" in summary
    assert "heist" in summary
    print("validate_outgunned_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
