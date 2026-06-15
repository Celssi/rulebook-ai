#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.apothecaria.curated import (
    all_ranks_valid,
    format_ailment_draw,
    format_forage_draw,
    format_patient_type_draw,
    lookup_ailment,
    lookup_reagent,
    parse_playing_card,
    reputation_tier,
    silver_base_rate,
)

def main() -> int:
    all_ranks_valid()
    assert parse_playing_card("J of hearts")["rank_key"] == "jack"
    assert parse_playing_card("A of spades")["rank_key"] == "ace"
    # PDF p.12 novice: 2 = Phodothropy
    ail = lookup_ailment(5, "2")
    assert ail["name"] == "Phodothropy", ail
    assert "CURSE" in ail["tags"]
    # PDF p.5 patient types
    patient = format_patient_type_draw("Queen of hearts")
    assert patient["patient_type"] == "Villager"
    # PDF p.34 village ace event
    forage = format_forage_draw("Ace of clubs", "village")
    assert "fountain" in forage["event"].lower()
    draw = format_ailment_draw("4 of diamonds", 5)
    assert draw["name"] == "Dragon Sickness"
    assert reputation_tier(5) == "novice"
    assert reputation_tier(15) == "intermediate"
    assert silver_base_rate(5) == 15
    assert silver_base_rate(33) == 50
    reg = lookup_reagent("Shieldcap")
    assert reg is not None
    assert reg["locales"].get("glimmerwood") == 2
    print("validate_apothecaria_curated: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
