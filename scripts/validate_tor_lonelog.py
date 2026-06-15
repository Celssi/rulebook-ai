#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.tor import play as _tor_play  # noqa: F401
from src.games.tor.entity import TorHero, format_summary, hero_from_dict, hero_to_dict


def main() -> int:
    hero = TorHero(
        name="Aragorn",
        culture="dunedain",
        calling="Wanderer",
        hope=12,
        dread=2,
        eye_awareness=1,
        patron="gilraen",
        safe_haven="Rivendell",
        journey_day=3,
    )
    hero.clamp()
    data = hero_to_dict(hero)
    restored = hero_from_dict(data)
    assert restored.name == "Aragorn"
    assert restored.patron == "gilraen"
    assert restored.journey_day == 3
    summary = format_summary(restored)
    assert "Aragorn" in summary
    assert "3" in summary
    print("validate_tor_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
