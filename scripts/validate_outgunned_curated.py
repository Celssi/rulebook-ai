#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import fitz

from src.games.outgunned.curated import (
    all_ad_prompts_valid,
    bump_tension,
    lookup_mission,
    lookup_table,
    reset_tension,
    roll_ad_prompt,
    roll_hurdle,
    roll_mission,
    roll_scene_drama,
    roll_villain_traits,
)
from src.games.outgunned.actions import run_shortcut


def main() -> int:
    assert all_ad_prompts_valid()
    prompt = roll_ad_prompt()
    assert prompt.get("text")
    # Adventure hurdle table (AD s. 35)
    assert "Dangerous locals" in lookup_table("hurdles_adventure", "2")
    assert "Key is at risk" in lookup_table("hurdles_adventure", "4")
    hurdle = roll_hurdle(variant="adventure")
    assert hurdle
    # Core hurdle preserved
    assert "Criminal turf" in lookup_table("hurdles", "2")
    # p.20 climax table
    assert "Betrayal" in lookup_table("climaxes", "5")
    drama = roll_scene_drama()
    assert drama["subject"] and drama["sense"] and drama["snag"]
    m = lookup_mission("1")
    assert m["type"] == "Deliver item"
    mission = roll_mission()
    assert mission.get("type")
    villain = roll_villain_traits()
    assert villain["nature"] and villain["desire"] and villain["problem"]

  # PDF text spot-check
    ad = fitz.open(ROOT / "docs/outgunned/assistant_director.pdf")
    full_text = "\n".join(ad[i].get_text() for i in range(ad.page_count))
    for part in ("Dangerous locals", "Scene Drama", "Deliver item"):
        assert part in full_text, part

    print("validate_outgunned_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
