#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.apothecaria.cottage import cottage_from_dict, cottage_to_dict, default_cottage
from src.games.apothecaria.lonelog import log_draw, read_tail
from src.games.apothecaria.play import get_apothecaria_store
from src.games.apothecaria.roster import create_cottage, delete_cottage


def main() -> int:
    store = get_apothecaria_store()
    store.ensure_initialized()
    cottage = create_cottage("Test Witch")
    cid = cottage.id
    assert cottage_from_dict(cottage_to_dict(cottage)).name == "Test Witch"
    log_draw(cid, "ailment", "2 of hearts", "Phodothropy")
    lines = read_tail(cid, 5)
    assert any("d:" in ln for ln in lines)
    delete_cottage(cid)
    print("validate_apothecaria_lonelog: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
