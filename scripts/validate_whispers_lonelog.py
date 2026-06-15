#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.whispers.investigation import (
    WhispersInvestigation,
    investigation_from_dict,
    investigation_to_dict,
)
from src.games.whispers.lonelog import format_whisper_draw_line


def main() -> int:
    inv = WhispersInvestigation(investigator_name="Mara", location_name="Old Museum", turn_number=2)
    d = investigation_to_dict(inv)
    assert investigation_from_dict(d).investigator_name == "Mara"
    line = format_whisper_draw_line(inv, "5 of hearts", "hearts")
    assert "d:" in line.lower() or "5" in line
    print("validate_whispers_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
