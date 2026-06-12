#!/usr/bin/env python3
"""Validate generic play saves and Lonelog v1.5 formatters (no Ollama)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.games.saves import (
    CampaignHeader,
    LonelogStore,
    PlayProfile,
    PlaySession,
    RosterStore,
    card_short_label,
    format_block,
    format_dice_from_result,
    format_dice_roll,
    format_draw,
    format_foe,
    format_generator,
    format_inv,
    format_mechanical,
    format_meta_note,
    format_narrative,
    format_npc,
    format_pc,
    format_player_action,
    format_resolution,
    format_resource_block,
    format_room,
    format_scene,
    format_session_header,
    format_table,
    format_thread,
    format_wealth,
    game_saves_dir,
    register_play_profile,
)
from src.games.saves import lonelog as lonelog_fmt
from src.games.saves.play_store import PlayStore
from src.games.saves.storage import roster_path
from src.play_tools import roll_dice


def test_core_formatters() -> None:
    assert format_player_action("Pick the lock") == "@ Pick the lock"
    assert format_player_action("Covers the door", actor="Jonah") == "@(Jonah) Covers the door"
    assert lonelog_fmt.format_oracle_question("Is anyone inside?") == "? Is anyone inside?"
    assert format_resolution("Yes, but...") == "-> Yes, but..."
    assert format_draw(["5 of hearts"]).startswith("d:")
    assert format_mechanical("Morale -1").startswith("->")
    assert format_narrative("The path narrows").startswith("=>")
    assert card_short_label("queen of hearts") == "Q♥"
    assert format_meta_note("revisit thread next session").startswith("(note:")


def test_dice_formatters() -> None:
    line = format_dice_roll("2d6", rolls=[3, 5], total=8, vs=7, outcome="Success")
    assert line == "d: 2d6=[3, 5] = 8 vs TN 7 -> Success"

    result = roll_dice("2d6+1")
    assert result["ok"]
    dice_line = format_dice_from_result(result)
    assert dice_line.startswith("d: 2d6+1=")
    assert str(result["total"]) in dice_line


def test_tags_and_structure() -> None:
    assert format_npc("Jonah", "friendly", "wounded") == "[N:Jonah|friendly|wounded]"
    assert format_pc("Alex", "HP 8", "Stress 0") == "[PC:Alex|HP 8|Stress 0]"
    assert format_thread("Find the lighthouse", "Open") == "[Thread:Find the lighthouse|Open]"
    assert format_foe("Thug A", "HP 6", "Close") == "[F:Thug A|HP 6|Close]"
    assert format_inv("Torch", "3") == "[Inv:Torch|3]"
    assert format_wealth("Gold 45", "Silver 12") == "[Wealth:Gold 45|Silver 12]"
    assert format_room("4", "active", "storage room", exits="S:R2, E:R5") == (
        "[R:4|active|storage room|exits S:R2, E:R5]"
    )
    assert format_scene(1, "Dark alley, midnight") == "S1 *Dark alley, midnight*"
    assert format_block("COMBAT") == "[COMBAT]"
    assert format_block("COMBAT", close=True) == "[/COMBAT]"


def test_oracle_and_tables() -> None:
    assert format_table("Mythic Event", "NPC Action", roll="d100=78") == (
        "tbl: Mythic Event d100=78 -> NPC Action"
    )
    assert "Tense" in format_table("Mood", "Uncanny", options=["Tense", "Uncanny"])
    gen = format_generator("NPC", "Merchant / Secretive", axes={"Role": "d6=2 -> Merchant"})
    assert gen.startswith("gen: NPC")


def test_resource_block() -> None:
    block = format_resource_block(
        [format_pc("Kael", "HP 12", "Supply d6"), format_inv("Torch", "2")]
    )
    assert block[0] == "[RESOURCES]"
    assert block[-1] == "[/RESOURCES]"


def test_campaign_header() -> None:
    yaml = CampaignHeader(title="Test Campaign", ruleset="Brambletrek", game_id="brambletrek").to_yaml()
    assert yaml.startswith("---")
    assert "title: Test Campaign" in yaml


def test_session_header() -> None:
    lines = format_session_header(1, date_str="2025-09-03", duration="1h30")
    assert lines[0] == "## Session 1"
    assert "2025-09-03" in lines[1]


def test_roster_and_lonelog(tmp: Path) -> None:
    game_id = "test_game"

    def entity_from_dict(data):
        return data or {"name": ""}

    roster = RosterStore(
        game_id,
        entity_filename="entity.json",
        default_slot_name="Hero",
        entity_from_dict=entity_from_dict,
        entity_to_dict=lambda e: e,
        default_entity=lambda: {"name": ""},
        slot_display_name=lambda e: e.get("name") or "Hero",
    )
    entity = roster.create_slot("Test Hero")
    slot_id = entity["id"]

    log = LonelogStore(game_id, game_label="Test Game")
    log.append(slot_id, format_draw(["3 of clubs"]), display_name="Test Hero")
    log.append_scene(slot_id, 1, "Starting scene", display_name="Test Hero")
    assert "3 of clubs" in log.recent_context(slot_id)
    assert "S1" in log.read_tail(slot_id)[-1]


def test_play_store_logging(tmp: Path) -> None:
    game_id = "demo_game"

    profile = PlayProfile(
        game_id=game_id,
        game_label="Demo",
        slot_label="Hero",
        default_slot_name="Hero",
        entity_from_dict=lambda d: d or {"name": "", "id": ""},
        entity_to_dict=lambda e: e,
        default_entity=lambda: {"name": "", "id": ""},
        slot_display_name=lambda e: e.get("name") or "Hero",
        lonelog_display_name=lambda e: e.get("name") or "Hero",
        play_settings={"story_mode": {"default": "player", "choices": ["player", "ai_narrator"]}},
        session_extra_keys=["pending_journey"],
    )
    register_play_profile(profile)
    roster_path(game_id).parent.mkdir(parents=True, exist_ok=True)

    store = PlayStore(profile)
    entity = store.create_slot("Ada")
    slot_id = entity["id"]

    roll = roll_dice("d6")
    store.log_roll(slot_id, "", result=roll)
    store.log_resolution(slot_id, "Yes, but...")
    store.log_oracle_question(slot_id, "Is anyone home?")
    store.log_block(slot_id, "COMBAT", [format_foe("Guard", "HP 5", "Close")])

    tail = store.read_log_tail(slot_id)
    assert any(ln.startswith("d: 1d6=") for ln in tail)
    assert any(ln.startswith("-> Yes") for ln in tail)
    assert any(ln.startswith("? Is anyone") for ln in tail)
    assert any(ln == "[COMBAT]" for ln in tail)

    session = PlaySession(
        settings={"story_mode": "player"},
        extra={"pending_journey": {"cards": ["5 of hearts"]}},
        messages=[{"role": "user", "content": "hello"}],
    )
    from src.games.saves.session import save_session

    save_session(game_id, slot_id, session)
    loaded = PlaySession.from_dict(
        __import__("json").loads(
            (game_saves_dir(game_id) / slot_id / "session.json").read_text(encoding="utf-8")
        )
    )
    assert loaded.extra["pending_journey"]["cards"] == ["5 of hearts"]


def test_brambletrek_profile_registered() -> None:
    from src.games.brambletrek import play as bt_play
    from src.games.brambletrek.lonelog import format_resources, format_scene_header
    from src.games.brambletrek.character import default_character
    from src.games.saves import get_play_store

    assert get_play_store(bt_play.GAME_ID) is not None
    char = default_character()
    char.journey_day = 2
    assert format_scene_header(char).startswith("S2 *")
    assert format_resources(10, 8, 7, name="Pip") == "[PC:Pip|Health 10|Morale 8|Supplies 7]"


def main() -> int:
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_core_formatters()
        test_dice_formatters()
        test_tags_and_structure()
        test_oracle_and_tables()
        test_resource_block()
        test_campaign_header()
        test_session_header()
        test_roster_and_lonelog(tmp / "a")
        test_play_store_logging(tmp / "b")
        test_brambletrek_profile_registered()
    print("All play-save checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
