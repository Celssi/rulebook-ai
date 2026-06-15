#!/usr/bin/env python3
"""Validate game shortcut matching and static shortcut execution (no Ollama)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import GAME_APOTHECARIA, GAME_BRAMBLETREK, GAME_COLOSTLE, GAME_LIGHTHOUSE, GAME_SANSIBILIA, GAME_WHISPERS
from src.games.apothecaria.actions import (
    SHORTCUT_IDS as APO_SHORTCUT_IDS,
    match_apothecaria_shortcut,
    run_shortcut as apo_run_shortcut,
)
from src.games.brambletrek.actions import (
    BRAMBLETREK_SHORTCUTS,
    match_brambletrek_shortcut,
    run_shortcut as bt_run_shortcut,
    shortcuts_for_character,
)
from src.games.sansibilia.actions import (
    SHORTCUT_IDS,
    SHORTCUTS,
    match_sansibilia_shortcut,
    run_shortcut as ss_run_shortcut,
    shortcuts_for_visit,
)
from src.games.lighthouse.actions import (
    SHORTCUT_IDS as LH_SHORTCUT_IDS,
    match_lighthouse_shortcut,
    run_shortcut as lh_run_shortcut,
)
from src.games.whispers.actions import (
    SHORTCUT_IDS as WH_SHORTCUT_IDS,
    match_whispers_shortcut,
    run_shortcut as wh_run_shortcut,
    shortcuts_for_investigation,
)
from src.games.ashes.actions import (
    SHORTCUT_IDS as ASHES_SHORTCUT_IDS,
    match_ashes_shortcut,
    run_shortcut as ashes_run_shortcut,
)
from src.games.colostle.actions import (
    SHORTCUT_IDS as COLOSTLE_SHORTCUT_IDS,
    match_colostle_shortcut,
    run_shortcut as col_run_shortcut,
)
from src.games.sansibilia.visit import SansibiliaVisit, visit_to_dict
from src.play_tools import clear_deck_store, reset_deck


def test_sansibilia_match() -> None:
    assert match_sansibilia_shortcut("draw character please") == "draw_character"
    assert match_sansibilia_shortcut("draw two cards") == "draw_character"
    assert match_sansibilia_shortcut("draw day's cards") == "draw_day"
    assert match_sansibilia_shortcut("daily draw for my journal") == "draw_day"
    assert match_sansibilia_shortcut("day 1 journal") == "day_one_prompts"
    assert match_sansibilia_shortcut("ending prompts") == "ending_prompts"
    assert match_sansibilia_shortcut("roll days between entries") == "roll_days_between"
    assert match_sansibilia_shortcut("city change rules") == "city_change_help"
    assert match_sansibilia_shortcut("unrelated question") is None


def test_brambletrek_match() -> None:
    assert match_brambletrek_shortcut("today's journey cards", active_adventure="") == "journey_day"
    assert (
        match_brambletrek_shortcut("today's journey cards", active_adventure="pumpkin_party")
        == "adventure_scene"
    )
    assert match_brambletrek_shortcut("combat setup please") == "combat_setup"
    assert match_brambletrek_shortcut("random character") == "random_character"
    assert match_brambletrek_shortcut("how do i start playing") == "start_playing"
    assert match_brambletrek_shortcut("story ending") == "reason_ending"


def test_sansibilia_static_run() -> None:
    clear_deck_store()
    reset_deck(game_id=GAME_SANSIBILIA, char_id="shortcut_test")

    day1 = ss_run_shortcut("day_one_prompts")
    assert day1.get("static") is True
    assert "Day 1 journal prompts" in day1["user_message"]
    assert day1["user_message"].count("- ") >= 3

    ending = ss_run_shortcut("ending_prompts")
    assert ending.get("static") is True
    assert "End of Your Stay" in ending["user_message"]

    roll = ss_run_shortcut("roll_days_between")
    assert roll.get("static") is True
    assert roll.get("dice", {}).get("ok") is True
    assert "Days between entries" in roll["user_message"]

    city = ss_run_shortcut("city_change_help")
    assert not city.get("static")
    assert "city changes" in city["prompt"].lower()

    char = ss_run_shortcut(
        "draw_character",
        game_id=GAME_SANSIBILIA,
        char_id="shortcut_test",
    )
    assert char.get("static") is True
    assert "Character draw" in char["user_message"]
    assert len(char.get("cards") or []) == 2

    day = ss_run_shortcut(
        "draw_day",
        game_id=GAME_SANSIBILIA,
        char_id="shortcut_test",
        visit_day=2,
    )
    assert "Day 2 draw" in day["user_message"]
    assert len(day.get("cards") or []) == 2
    assert day.get("prompt")

    clear_deck_store()


def test_sansibilia_visit_shortcut_lists() -> None:
    active = {s["id"] for s in shortcuts_for_visit(visit_complete=False)}
    assert active == SHORTCUT_IDS
    ended = {s["id"] for s in shortcuts_for_visit(visit_complete=True)}
    assert ended == {"ending_prompts", "city_change_help"}


def test_brambletrek_static_run() -> None:
    clear_deck_store()
    reset_deck(game_id=GAME_BRAMBLETREK, char_id="shortcut_test")

    help_msg = bt_run_shortcut(
        "adventure_overview",
        game_id=GAME_BRAMBLETREK,
        active_adventure="",
    )
    assert help_msg["kind"] == "static"
    assert "Active adventure" in help_msg["user_message"]

    scene_help = bt_run_shortcut(
        "adventure_scene",
        game_id=GAME_BRAMBLETREK,
        active_adventure="",
    )
    assert scene_help["kind"] == "static"
    assert "pick an active adventure" in scene_help["user_message"].lower()

    legacy = bt_run_shortcut(
        "random_legacy",
        game_id=GAME_BRAMBLETREK,
        char_id="shortcut_test",
    )
    assert legacy["kind"] == "roll_rag"
    assert "d6" in legacy["user_message"].lower() or "Legacy" in legacy["user_message"]

    journey = bt_run_shortcut(
        "journey_day",
        game_id=GAME_BRAMBLETREK,
        char_id="shortcut_test",
    )
    assert journey["kind"] == "multi_draw_rag"
    assert len(journey.get("journey_cards") or []) == 4

    clear_deck_store()


def test_brambletrek_sidebar_filter() -> None:
    without_adv = {s["id"] for s in shortcuts_for_character(active_adventure="")}
    assert "adventure_scene" not in without_adv
    assert "journey_day" in without_adv

    with_adv = {s["id"] for s in shortcuts_for_character(active_adventure="pumpkin_party")}
    assert "adventure_scene" in with_adv


def test_sansibilia_run_visit_shortcut_static() -> None:
    from src.games.sansibilia.play_handlers import run_visit_shortcut
    from src.games.saves.context import PlayContext

    visit = SansibiliaVisit(id="visit_shortcut_test", name="Test")
    ctx = PlayContext(
        game_id=GAME_SANSIBILIA,
        slot_id=visit.id,
        entity=visit_to_dict(visit),
        settings={"ending_mode": "four_changes", "card_source": "virtual"},
    )

    user_msg, answer, sources, route = run_visit_shortcut(
        ctx,
        "day_one_prompts",
        chat_provider="ollama",
        retrieval_cfg={"use_hybrid": True},
        top_k=5,
        factions=[],
    )
    assert route == "sansibilia:day_one_prompts"
    assert user_msg == answer
    assert sources == []
    assert "Day 1 journal prompts" in answer

    try:
        run_visit_shortcut(
            ctx,
            "not_a_shortcut",
            chat_provider="ollama",
            retrieval_cfg={},
            top_k=5,
            factions=[],
        )
        raise AssertionError("expected ValueError for unknown shortcut")
    except ValueError:
        pass


def test_shortcut_catalog() -> None:
    bt_ids = {s["id"] for s in BRAMBLETREK_SHORTCUTS}
    assert len(bt_ids) == len(BRAMBLETREK_SHORTCUTS)
    ss_ids = {s["id"] for s in SHORTCUTS}
    assert ss_ids == SHORTCUT_IDS


def test_lighthouse_match() -> None:
    assert match_lighthouse_shortcut("light the lamp") == "light_lamp"
    assert match_lighthouse_shortcut("maintenance task") == "maintenance"
    assert match_lighthouse_shortcut("beachcombing") == "beachcombing"


def test_lighthouse_static_run() -> None:
    clear_deck_store()
    reset_deck(game_id=GAME_LIGHTHOUSE, char_id="shortcut_test")
    weather = lh_run_shortcut("weather")
    assert weather.get("static") is True
    assert "weather" in weather["user_message"].lower()
    order = lh_run_shortcut("order_of_play")
    assert "Order of play" in order["user_message"]
    clear_deck_store()


def test_lighthouse_shortcut_ids() -> None:
    assert "light_lamp" in LH_SHORTCUT_IDS
    assert "beachcombing" in LH_SHORTCUT_IDS


def test_apothecaria_match() -> None:
    assert match_apothecaria_shortcut("draw ailment") == "draw_ailment"
    assert match_apothecaria_shortcut("forage in the forest") == "forage_event"
    assert match_apothecaria_shortcut("patient type") == "draw_patient_type"
    assert match_apothecaria_shortcut("new patient") == "start_patient"
    assert match_apothecaria_shortcut("complete potion") == "complete_potion"


def test_apothecaria_static_run() -> None:
    clear_deck_store()
    reset_deck(game_id=GAME_APOTHECARIA, char_id="shortcut_test")
    rules = apo_run_shortcut("foraging_rules")
    assert rules.get("static") is True
    assert "Foraging" in rules["user_message"]
    patient = apo_run_shortcut(
        "draw_patient_type",
        game_id=GAME_APOTHECARIA,
        char_id="shortcut_test",
    )
    assert patient.get("static") is True
    assert "Patient type" in patient["user_message"]
    preview = apo_run_shortcut("potion_preview")
    assert preview.get("static") is True
    assert "Potion preview" in preview["user_message"]
    ailment = apo_run_shortcut(
        "draw_ailment",
        game_id=GAME_APOTHECARIA,
        char_id="shortcut_test",
        cards=["7 of hearts"],
        reputation=5,
    )
    assert "Ailment draw" in ailment["user_message"]
    assert "timer" in ailment["prompt"].lower()
    clear_deck_store()


def test_apothecaria_shortcut_ids() -> None:
    assert "draw_ailment" in APO_SHORTCUT_IDS
    assert "forage_event" in APO_SHORTCUT_IDS
    assert "start_patient" in APO_SHORTCUT_IDS
    assert "complete_potion" in APO_SHORTCUT_IDS
    assert "witch_clue" in APO_SHORTCUT_IDS


def test_whispers_match() -> None:
    assert match_whispers_shortcut("build whispers deck") == "build_deck"
    assert match_whispers_shortcut("draw from whispers deck") == "draw_whisper"
    assert match_whispers_shortcut("oracle question") == "oracle"
    assert match_whispers_shortcut("deck rules") == "deck_rules"


def test_whispers_static_run() -> None:
    built = wh_run_shortcut("build_deck", difficulty="normal", extra_secrets=0)
    assert built.get("static") is True
    assert "Location draw" in built["user_message"]
    deck = list(built["deck"])
    drawn = wh_run_shortcut("draw_whisper", whispers_deck=deck, jokers_drawn=0)
    assert "Whisper draw" in drawn["user_message"] or "Final draw" in drawn["user_message"]
    oracle = wh_run_shortcut("oracle")
    assert oracle.get("static") is True
    assert "Oracle" in oracle["user_message"]


def test_whispers_shortcut_lists() -> None:
    assert shortcuts_for_investigation(deck_built=False)
    assert shortcuts_for_investigation(deck_built=True, investigation_complete=True)


def test_ashes_match() -> None:
    assert match_ashes_shortcut("draw room card") == "draw_room"
    assert match_ashes_shortcut("draw room and journal") == "draw_room_journal"
    assert match_ashes_shortcut("draw journal prompt") == "draw_journal"
    assert match_ashes_shortcut("draw enemy") == "draw_enemy"
    assert match_ashes_shortcut("sanctuary check") == "sanctuary_check"
    assert match_ashes_shortcut("navigation roll") == "navigate"
    assert match_ashes_shortcut("fate's gift") == "character_gift"
    assert match_ashes_shortcut("draw 4 trials") == "draw_starting_trials"
    assert match_ashes_shortcut("draw new trial") == "draw_trial"
    assert match_ashes_shortcut("boss entry") == "boss_entry"
    assert match_ashes_shortcut("roll melee weapon") == "roll_melee_weapon"


def test_ashes_static_run() -> None:
    out = ashes_run_shortcut("sanctuary_check")
    assert out.get("static")
    assert "Sanctuary" in out["user_message"]
    out2 = ashes_run_shortcut("dungeon_rules")
    assert "Dungeon layout" in out2["user_message"]
    trials = ashes_run_shortcut("draw_starting_trials")
    assert trials.get("replace_trials")
    assert len(trials.get("cards") or []) == 4
    ember = ashes_run_shortcut("ember_help", level=2)
    assert "Ember" in ember["user_message"]


def test_colostle_match() -> None:
    assert match_colostle_shortcut("exploration phase") == "exploration_phase"
    assert match_colostle_shortcut("draw calling") == "draw_character"
    assert match_colostle_shortcut("oracle question") == "oracle"


def test_colostle_static_run() -> None:
    clear_deck_store()
    reset_deck(game_id=GAME_COLOSTLE, char_id="shortcut_test")
    classes = col_run_shortcut("classes_help")
    assert classes.get("static") is True
    assert "Armed" in classes["user_message"]
    item = col_run_shortcut(
        "draw_item",
        game_id=GAME_COLOSTLE,
        char_id="shortcut_test",
        cards=["5 of hearts"],
    )
    assert item.get("static") is not True
    assert "journal scene" in item["prompt"].lower()
    event = col_run_shortcut(
        "draw_event",
        game_id=GAME_COLOSTLE,
        char_id="shortcut_test",
        cards=["9 of spades"],
    )
    assert event.get("static") is not True
    assert "journal scene" in event["prompt"].lower()
    clear_deck_store()


def test_colostle_shortcut_ids() -> None:
    assert "exploration_phase" in COLOSTLE_SHORTCUT_IDS
    assert "combat_rook" in COLOSTLE_SHORTCUT_IDS


def test_lighthouse_narrator_routing() -> None:
    from unittest.mock import patch

    from src.games.lighthouse.play_handlers import run_watch_shortcut
    from src.games.lighthouse.watch import KeeperWatch, watch_to_dict
    from src.games.saves.context import PlayContext

    watch = KeeperWatch(id="lh_routing_test", name="Test Keeper")
    base_kwargs = dict(
        chat_provider="ollama",
        retrieval_cfg={"use_hybrid": True},
        top_k=5,
        factions=[],
        beachcombing_hour=10,
    )

    clear_deck_store()
    reset_deck(game_id=GAME_LIGHTHOUSE, char_id=watch.id)

    ctx_player = PlayContext(
        game_id=GAME_LIGHTHOUSE,
        slot_id=watch.id,
        entity=watch_to_dict(watch),
        settings={"card_source": "virtual", "story_mode": "player"},
    )
    user_msg, answer, _, route = run_watch_shortcut(ctx_player, "beachcombing", **base_kwargs)
    assert route == "lighthouse:beachcombing"
    assert user_msg == answer
    assert "Beachcombing" in user_msg

    ctx_narrator = PlayContext(
        game_id=GAME_LIGHTHOUSE,
        slot_id=watch.id,
        entity=watch_to_dict(watch),
        settings={"card_source": "virtual", "story_mode": "ai_narrator"},
    )
    with patch(
        "src.games.lighthouse.play_handlers._maybe_ai_prose",
        return_value="Mock logbook prose for the tide.",
    ):
        user_msg2, answer2, _, _ = run_watch_shortcut(ctx_narrator, "beachcombing", **base_kwargs)
    assert user_msg2 != answer2
    assert answer2 == "Mock logbook prose for the tide."

    with patch(
        "src.games.lighthouse.play_handlers._maybe_ai_prose",
        return_value="The lamp catches flame.",
    ):
        _, lamp_answer, _, _ = run_watch_shortcut(
            ctx_narrator,
            "light_lamp",
            chat_provider="ollama",
            retrieval_cfg={"use_hybrid": True},
            top_k=5,
            factions=[],
        )
    assert lamp_answer == "The lamp catches flame."

    clear_deck_store()


def test_colostle_narrator_routing() -> None:
    from unittest.mock import patch

    from src.games.colostle.character import ColostleCharacter, character_to_dict
    from src.games.colostle.play_handlers import run_character_shortcut
    from src.games.saves.context import PlayContext

    char = ColostleCharacter(id="col_routing_test", name="Test Adventurer")
    base_kwargs = dict(
        chat_provider="ollama",
        retrieval_cfg={"use_hybrid": True},
        top_k=5,
        factions=[],
    )

    clear_deck_store()
    reset_deck(game_id=GAME_COLOSTLE, char_id=char.id)

    ctx_player = PlayContext(
        game_id=GAME_COLOSTLE,
        slot_id=char.id,
        entity=character_to_dict(char),
        settings={"card_source": "virtual", "story_mode": "player", "location_mode": "roomlands"},
    )
    user_msg, answer, _, route = run_character_shortcut(ctx_player, "draw_item", **base_kwargs)
    assert route == "colostle:draw_item"
    assert user_msg == answer

    ctx_narrator = PlayContext(
        game_id=GAME_COLOSTLE,
        slot_id=char.id,
        entity=character_to_dict(char),
        settings={"card_source": "virtual", "story_mode": "ai_narrator", "location_mode": "roomlands"},
    )
    with patch(
        "src.games.colostle.play_handlers._maybe_ai_prose",
        return_value="Mock journal prose for the item.",
    ):
        user_msg2, answer2, _, _ = run_character_shortcut(ctx_narrator, "draw_item", **base_kwargs)
    assert user_msg2 != answer2
    assert answer2 == "Mock journal prose for the item."

    clear_deck_store()


def main() -> int:
    test_shortcut_catalog()
    test_sansibilia_match()
    test_brambletrek_match()
    test_sansibilia_static_run()
    test_sansibilia_visit_shortcut_lists()
    test_brambletrek_static_run()
    test_brambletrek_sidebar_filter()
    test_sansibilia_run_visit_shortcut_static()
    test_lighthouse_shortcut_ids()
    test_lighthouse_match()
    test_lighthouse_static_run()
    test_apothecaria_shortcut_ids()
    test_apothecaria_match()
    test_apothecaria_static_run()
    test_whispers_match()
    test_whispers_static_run()
    test_whispers_shortcut_lists()
    test_ashes_match()
    test_ashes_static_run()
    _ = ASHES_SHORTCUT_IDS
    test_colostle_shortcut_ids()
    test_colostle_match()
    test_colostle_static_run()
    test_lighthouse_narrator_routing()
    test_colostle_narrator_routing()
    print("validate_shortcuts: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
