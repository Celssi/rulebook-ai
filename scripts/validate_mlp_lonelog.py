#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.mlp.entity import MlpPony, format_summary, pony_from_dict, pony_to_dict


def main() -> int:
    pony = MlpPony(
        pony_name="Pinkie Pie",
        name="Pinkie Pie",
        origin="earth_pony",
        role="spirit_of_laughter",
        influences=["party_maestro", "chatty"],
        hang_ups=["Every problem needs a party."],
        base_essences={"strength": 3, "speed": 3, "smarts": 3, "social": 3},
        cutie_mark="Balloons",
        friendship_points=1,
    )
    pony.clamp()
    raw = pony_to_dict(pony)
    restored = pony_from_dict(raw)
    assert restored.pony_name == "Pinkie Pie"
    assert restored.origin == "earth_pony"
    assert restored.role == "spirit_of_laughter"
    assert sum(restored.essences.values()) == 16
    summary = format_summary(restored)
    assert "Pinkie Pie" in summary
    assert "Earth Pony" in summary
    print("validate_mlp_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
