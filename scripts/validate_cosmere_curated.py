#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.cosmere.curated import all_faces_valid, format_plot_dice_roll, lookup_plot_face
from src.games.gm_solo.dice import roll_plot_dice


def main() -> int:
    assert all_faces_valid()
    comp = lookup_plot_face(1)
    assert comp["label"] == "complication"
    opp = lookup_plot_face(6)
    assert opp["label"] == "opportunity"
    formatted = format_plot_dice_roll([1, 4, 6])
    assert "complication" in formatted.lower()
    assert "opportunity" in formatted.lower()
    result = roll_plot_dice(2)
    assert len(result["rolls"]) == 2
    assert "complication" in result["labels"] or "opportunity" in result["labels"] or "neutral" in result["labels"]
    print("validate_cosmere_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
