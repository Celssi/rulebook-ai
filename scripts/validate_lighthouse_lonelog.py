#!/usr/bin/env python3
"""Smoke-test Lighthouse Lonelog formatters."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.games.lighthouse.lonelog import format_night_header
from src.games.lighthouse.watch import KeeperWatch, watch_from_dict, watch_to_dict


def main() -> int:
    watch = KeeperWatch(name="Keeper", night_count=2)
    header = format_night_header(watch)
    assert "Night 2" in header
    assert "Lighthouse" in header

    roundtrip = watch_from_dict(watch_to_dict(watch))
    assert roundtrip.name == "Keeper"
    assert roundtrip.night_count == 2

    print("validate_lighthouse_lonelog: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
