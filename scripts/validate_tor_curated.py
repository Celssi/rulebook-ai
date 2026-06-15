#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.tor.curated import (
    all_tables_valid,
    format_hunt_threshold,
    format_milestones_table,
    lookup_fortune,
    lookup_hunt_threshold,
    lookup_journey_event_detail,
    lookup_lore,
    lookup_patron,
    lookup_revelation_episode,
    resolve_telling,
    roll_journey_event,
    roll_lore_draw,
    roll_patron_quest,
    roll_revelation_episode,
)
from src.games.gm_solo.dice import roll_tor_skill


def main() -> int:
    assert all_tables_valid()

    # Telling Table — Strider Mode p.10
    yes = resolve_telling(8, "doubtful")
    assert yes["answer"] == "yes"
    no = resolve_telling(5, "doubtful")
    assert no["answer"] == "no"
    g = resolve_telling(11, "middling")
    assert g["answer"] == "yes" and g["feat_icon"] == "gandalf"

    # Fortune p.8
    f1 = lookup_fortune(1, ill=False)
    assert "bypass a threat" in f1["text"].lower()
    eye_down = lookup_fortune(11, ill=False)
    assert eye_down["eye_awareness_delta"] == -1

    # Ill-Fortune p.8
    ill_eye = lookup_fortune(12, ill=True)
    assert ill_eye["eye_awareness_delta"] == 2

    # Lore appendix
    lore = lookup_lore(1, 1)
    assert lore["action"] == "Aid"
    draw = roll_lore_draw()
    assert draw["phrase"]

    # Patron quests pp.26-28
    bilbo = lookup_patron("bilbo")
    assert len(bilbo["quests"]) == 6
    quest = roll_patron_quest("gandalf")
    assert quest["roll"] in range(1, 7)
    assert quest["quest"]

    skill = roll_tor_skill(2)
    assert "feat" in skill
    assert skill["success_count"] >= 0

    # Journey event details p.17-18, 25-26
    detail = lookup_journey_event_detail("despair", 1)
    assert detail["event"] == "Servants of the Enemy"
    assert "Noteworthy" in detail["outcome"]
    detail_cm = lookup_journey_event_detail("chance_meeting", 6)
    assert detail_cm["event"] == "Auspicious gathering"
    journey = roll_journey_event()
    assert journey.get("success_roll") in range(1, 7)
    assert journey.get("detail_event")

    # Experience milestones p.7
    ms = format_milestones_table()
    assert "Accept a mission from a patron" in ms
    assert "2 Skill Points" in ms

    # Hunt threshold p.26
    hunt = lookup_hunt_threshold("wild")
    assert hunt["threshold"] == 16
    hunt_fmt = format_hunt_threshold("border")
    assert "18" in hunt_fmt

    # Revelation episodes p.26
    rev = lookup_revelation_episode(4)
    assert "ambush" in rev["episode"].lower()
    rev_roll = roll_revelation_episode()
    assert rev_roll["episode"]

    print("validate_tor_curated: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
