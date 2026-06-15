#!/usr/bin/env python3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.games.ashes.lonelog import log_room, read_tail
from src.games.ashes.scion import AshesScion
from src.games.ashes.play import get_ashes_store


def main() -> int:
    store = get_ashes_store()
    scion = store.create_slot("Test Scion")
    slot_id = scion.id if hasattr(scion, "id") else str(scion.get("id", ""))
    assert slot_id
    entity = AshesScion(id=slot_id, name="Test Scion", rooms_cleared=2)
    log_room(slot_id, entity, "7 of hearts", "Labyrinth", "INT")
    lines = read_tail(slot_id, 10)
    assert any("Labyrinth" in ln for ln in lines)
    store.delete_slot(slot_id)
    print("validate_ashes_lonelog: OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
