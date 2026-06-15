#!/usr/bin/env python3
"""Build verified Apothecaria curated YAML from PDF-sourced text."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/curated"
RANKS = ("ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "jack", "queen", "king")

# Locale events transcribed from Apothecaria p.34–51
LOCALES: dict[str, dict[str, str]] = {
    "village": {
        "ace": "You take a seat by the town fountain and watch the water. As you sit there, someone joins you. Who is it? What happens?",
        "2": "A rumour is going around town. What is it? Is there any truth to it?",
        "3": "You see a bard busking outside The Copper Fox who has managed to drum up quite the crowd. What makes their music so interesting? Do you drop a Silver in their case?",
        "4": "An adventuring party is loudly planning their expedition into Hero's Hollow. They ask for your help. You can decline OR next time you go Foraging in Hero's Hollow, Decrease your Timer by 3.",
        "5": "The postal harpy drops a parcel into your arms. What is it? Who is it from?",
        "6": "The baker spots you passing and waves you over. They offer you bread and a Songberry.",
        "7": "The Museum of Magic requests one of each reagent for their collection. Tick M boxes as you send reagents.",
        "8": "Your familiar has gotten into a spot of bother with one of the villagers. What have they done?",
        "9": "Someone hands you a reagent they found on a hike. Draw a card and take a reagent of that value from any locale.",
        "10": "A village child trampled your Garden Plot. How do you react?",
        "jack": "You visit the Lunar Tower. Next time you go Foraging, start with 6 Foraging points.",
        "queen": "Another witch visits and invites you to lunch. What is their name and familiar?",
        "king": "A farmer lost their pigs. On non-face card events while foraging, flip a coin — tails means you found a pig and Decrease Timer by 1.",
    },
    "glimmerwood": {
        "ace": "You trip while fording a river and fall into the arms of a blushing naiad. Write about your relationship each time.",
        "2": "Thieving fairies grab your basket. Keep one reagent from this trip, discard the rest.",
        "3": "Boar tracks lead to a reagent. Draw a card and treat it as a PLANT of the same value.",
        "4": "A jealous truffle hunter shoots you. Decrease Timer by 1.",
        "5": "A druid tells you where to find a reagent. Draw a card and treat it as a PLANT of the same value.",
        "6": "You wander too near a bear's den and are chased. Lose 2 Foraging points.",
        "7": "Pixies challenge you to caber toss (3 cards each). Win: 10 Silver. Lose: give a reagent or be cursed.",
        "8": "Weaver's Wood — giant spiders whisper about eating you. Decrease Timer by 1.",
        "9": "A wounded animal by an oak. Draw on the Familiar list; heal its [WOUND] this Ailment for a Grove bonus.",
        "10": "Fairy circle fever. Lose 1 Foraging point.",
        "jack": "An amused elf on a golden throne asks for a gift in exchange for a story.",
        "queen": "A unicorn appears. Below rep 20 it vanishes; above 20 it gives a Face Value reagent.",
        "king": "The Glimmerwood Giant — asleep first time, angry if awakened again.",
    },
    "blastfire_bog": {
        "ace": "Goblins beset your coracle. Decrease Timer by 1.",
        "2": "Exploding bog moss covers you. Decrease Timer by 1.",
        "3": "A massive toad welcomes you with a poem. Write more each time.",
        "4": "A moss-covered statue in the swamp. Who is it of?",
        "5": "Your boat tips; leeches attach. Lose 2 Foraging points.",
        "6": "A crocodile person in an airboat offers a ride. Increase Timer by 2.",
        "7": "Goblin village welcomes you with a horrific meal.",
        "8": "Blastfire barrage. With a Wand, catch blastfire (decoration or 25 Silver).",
        "9": "Crashed airship in the canopy. What do you find inside?",
        "10": "Turtle island with a PLANT reagent. Draw a card for value.",
        "jack": "Dragon skeleton tells stories of its life.",
        "queen": "Mushroom spores connect you to a reagent network. Gain 4 Foraging points.",
        "king": "The Crownless King stag beetle tells history of the wooden palace.",
    },
    "meltwater_loch": {
        "ace": "Strange footprints on the beach. What can you tell?",
        "2": "Bird's nest with ANIMAL reagent. Draw for you vs bird; higher wins or lose 1 point.",
        "3": "Gull-drakes steal reagents. Keep 1, discard rest.",
        "4": "Worthless junk half-buried in sand.",
        "5": "Jovial dwarf fisherman points to best reagent spot. Draw card as Loch reagent.",
        "6": "Cù-sìth hunt — hide before the third bark. Decrease Timer by 1.",
        "7": "Ghost ship crew invites you aboard.",
        "8": "Bàs Bàta breaches. Lose 1 point for animal reagents, or get one if Shattered Tooth cured.",
        "9": "Practising siren offers a fish of your choice.",
        "10": "Skeleton over a barnacled chest on a wreck.",
        "jack": "Giant left a building-sized item on the shore.",
        "queen": "Message in a bottle with instructions to reply.",
        "king": "Bàs Bàta with Shattered Tooth. Make 10 spare Shattered Tooth potions to calm it, or Decrease Timer by 1.",
    },
    "dreamwater_depths": {
        "ace": "Marble fountain — dip Moonstone to recharge or take PURIFY vial.",
        "2": "Ancient ghost passes through you with a vision of the city.",
        "3": "Bioluminescent kelp reveals surroundings. Gain 4 Foraging points.",
        "4": "Massive gar chases you into a building. Decrease Timer by 1.",
        "5": "Colourful merfolk invites you to dance.",
        "6": "Kelpie lures you from shelter. Decrease Timer by 1.",
        "7": "Glowing crystal cave euphoria. Gain 4 Foraging points.",
        "8": "Ghostly snippet of music or speech from the ruins.",
        "9": "Ancient ghost vision. Lose 2 Foraging points.",
        "10": "Kelp forest — draw card as PLANT or ANIMAL.",
        "jack": "Amiable diver with floating camera trades reagent or knowledge.",
        "queen": "Dreamwater spray — vivid lucid dream. Decrease Timer by 2.",
        "king": "Sunken ship hold of sealed scrolls. Bring one intact scroll ashore.",
    },
    "moonbreaker_mountain": {
        "ace": "Lost sheep in a cave. Guide home: Decrease Timer by 2, add 3 Sweet to potion.",
        "2": "Billy goat chase — lose 1 point or 1 reagent.",
        "3": "Gull-drakes disturbed. Lose 2 Foraging points.",
        "4": "Wayfarer's Stone — a stranger from afar asks something.",
        "5": "Hot air balloonist offers a lift. Increase Timer by 1.",
        "6": "Half-way shrine on the trail.",
        "7": "Sphinx riddle on a rock podium.",
        "8": "Base camp adventurers leave a Dungeon reagent. Draw card for value.",
        "9": "Obvious reagent on outcrop. Draw card for value.",
        "10": "Wild gryphon dive. Lose 2 Foraging points.",
        "jack": "Damaged stone golem — repair 10 downtime segments to gain Golem Helper.",
        "queen": "Mountain giant invites you into their cave.",
        "king": "Summit dragon gives Moonstone and a constellation story.",
    },
    "cloud_isles": {
        "ace": "Stranded animal on an island. Escort home? Decrease Timer by 1.",
        "2": "Cloud shark scrape. Decrease Timer by 1.",
        "3": "Fall through clouds — drop all but 1 reagent.",
        "4": "Strange landed cottage. Who lives here?",
        "5": "Airship packet of reagents. Draw card as PLANT.",
        "6": "Skywhale song — next forage lowers Ambergris FV by 8.",
        "7": "Marooned sailor spells HELP. Rescue for 5 Silver.",
        "8": "Wyvern chase. Lose 3 Foraging points.",
        "9": "Flying familiar brings reagent of your choice.",
        "10": "Airship captain offers cloud tea.",
        "jack": "Aurora Lighthouse — bottle Aurora with Wand (decoration or 25 Silver).",
        "queen": "Old harpies know where your reagent is. Gain 4 Foraging points.",
        "king": "Minor god walks a rainbow and tells legends.",
    },
    "heros_hollow": {
        "ace": "Trap wounds you. Decrease Timer by 2.",
        "2": "Bone snap wakes the dead in a crypt.",
        "3": "Ancient object dropped by a fallen adventurer.",
        "4": "Little furry shopkeeper wants to trade.",
        "5": "Rough dungeon map. Draw card as Dungeon reagent.",
        "6": "Stone chute into a cell. Decrease Timer by 1.",
        "7": "Duel the Baron (3 cards vs 4). Win: reagent. Lose: 2 Foraging points.",
        "8": "Puzzle room — write the puzzle and solution.",
        "9": "Newbie adventurer offers 10 Silver to lead them out. Decrease Timer by 1.",
        "10": "Ruined library book excerpt.",
        "jack": "Begging mimic chest — feed 3 animal reagents to gain Mimic familiar.",
        "queen": "Bound demon in the centre chamber wants conversation.",
        "king": "Dark Ruler opens portal to The Strange.",
    },
    "the_strange": {
        "ace": "Blue horned demon offers disgusting stew.",
        "2": "Bone tower loop. Decrease Timer by 1; tourist map if first time.",
        "3": "Friendly demon pen-pals.",
        "4": "Chaos Well — draw card as MAGIC reagent.",
        "5": "Mechanical people with video messages.",
        "6": "Bazaar — buy any MAGIC reagent for 3 Silver × FV.",
        "7": "You meet yourself and receive the potion you need.",
        "8": "Glass-headed mechanical person shows reagent location. Draw ANY reagent.",
        "9": "City reshuffles; tourist map useless. Lose all Foraging points.",
        "10": "Walking tour sweeps you along. Decrease Timer by 1.",
        "jack": "Arena contest behind chain curtains.",
        "queen": "Great Demon offers a home for 1,000 Silver (tasks reduce cost by 50).",
        "king": "Normal-looking house by Skull Gate — another human lives here.",
    },
}

TOOLS = {
    "starter": [
        {"id": "mortar", "name": "Mortar and Pestle", "cost": 0, "prep": "CRUSH"},
        {"id": "cauldron", "name": "Cauldron", "cost": 0, "prep": "BOIL"},
        {"id": "alembic", "name": "Alembic", "cost": 0, "prep": "DISTIL"},
    ],
    "purchasable": [
        {"id": "sickle", "name": "Sickle", "cost": 50, "effect": "Foraging points +2 per miss instead of +1"},
        {"id": "wand", "name": "Wand", "cost": 100, "effect": "Collect certain MAGIC reagents"},
        {"id": "athame", "name": "Athame", "cost": 80, "effect": "Use Ritual Circle in village"},
        {"id": "broom", "name": "Broom", "cost": 100, "effect": "Fly to Cloud Isles", "unlocks": "cloud_isles"},
        {"id": "coracle", "name": "Coracle", "cost": 70, "effect": "Navigate Blastfire Bog", "unlocks": "blastfire_bog"},
    ],
    "special": [
        {"id": "golem", "name": "Golem Helper", "cost": None, "effect": "TEND / MAKE / SEARCH tasks per season"},
        {"id": "moonstone", "name": "Moonstone", "cost": None, "effect": "PURIFY potion (4 uses)"},
        {"id": "mimic", "name": "Mimic", "cost": None, "effect": "Activate village services remotely"},
        {"id": "tourist_map", "name": "Tourist Map", "cost": None, "effect": "Navigate The Strange"},
    ],
}

UPGRADES = [
    {"id": "garden_plot", "name": "Garden Plot", "cost": 100, "effect": "Grow 1 PLANT FV ≤8"},
    {"id": "hive", "name": "Hive", "cost": 50, "effect": "+1 SWEET to 4 potions per season"},
    {"id": "fish_tank", "name": "Fish Tank", "cost": 150, "effect": "2 fish types FV ≤8"},
    {"id": "paddock", "name": "Paddock", "cost": 300, "effect": "2 ANIMAL reagents FV ≤8"},
    {"id": "basement_hollow", "name": "Basement Hollow", "cost": 500, "effect": "Up to 5 Dungeon reagents free access"},
    {"id": "greenhouse", "name": "Glimmerwood Greenhouse", "cost": 500, "effect": "Up to 5 Forest reagents"},
    {"id": "meltwater_pond", "name": "Meltwater Pond", "cost": 500, "effect": "Up to 5 Loch reagents"},
    {"id": "mini_mountain", "name": "Mini Mountain", "cost": 500, "effect": "Up to 5 Mountain reagents"},
    {"id": "treatment_room", "name": "Treatment Room", "cost": 300, "effect": "All Timers +3; +10 Silver per success"},
    {"id": "spare_room", "name": "Spare Room", "cost": 500, "rep_min": 30, "effect": "Gain Apprentice"},
    {"id": "spirit_seal", "name": "Spirit Seal", "cost": 300, "effect": "Banish hauntings"},
    {"id": "travel_stone", "name": "Travel Stone", "cost": 200, "effect": "Link 2 locales — no timer cost between"},
    {"id": "raven_loft", "name": "Raven Loft", "cost": 150, "effect": "Remote patients — double Silver if both cured"},
]

VILLAGE = [
    {"id": "tavern", "name": "The Copper Fox Tavern", "cost": 0, "effect": "Socialise during Downtime"},
    {"id": "lunar_tower", "name": "Lunar Tower", "cost": 0, "effect": "Start next forage with 6 points"},
    {"id": "bits_bobs", "name": "Bits & Bobs", "cost": 0, "effect": "Buy tools and upgrades"},
    {"id": "ritual_circle", "name": "Ritual Circle", "cost": 0, "requires": "athame", "effect": "The Calling — gain familiar"},
]

FESTIVALS = {
    "spring": {"id": "flower_festival", "name": "Flower Festival", "prompts": [
        "Flower Festival Dance — who do you go with?",
        "Market finds — anything catch your eye?",
        "Baking contest (blackjack vs 3 face-down cards). Win: Sun Sugar (+3 Sweet).",
    ]},
    "summer": {"id": "sunrise_celebration", "name": "Sunrise Celebration", "prompts": [
        "Rowboat race — draw 2+2+2 cards; highest single card wins Bata's Oar.",
        "Ash Mother ritual with druids?",
        "Lowland merchants — what catches your eye?",
    ]},
    "autumn": {"id": "bogles_night", "name": "Bogle's Night", "prompts": [
        "Welcome the departed souls.",
        "Spooky Soiree — costume and companion?",
        "Lonely older spirits — do you talk to them?",
        "Village thanks you — 100 Silver and kind words.",
        "Bonfire shape — what did you add?",
    ]},
    "winter": {"id": "frostfall_festival", "name": "Frostfall Festival", "prompts": [
        "Feast dish — what do you bring?",
        "Snowball fight — 5 cards vs 4.",
        "Sled race down Breakneck — 10+ wins 20 Silver.",
        "Someone gives you a present.",
    ]},
}

WITCH_STORYLINE = {
    "first_steps": {
        "ace": "Learn the old witch's name (or true name).",
        "2": "Someone reminisces about the witch's personality.",
        "3": "Find what the witch looked like.",
        "4": "Find something the witch decorated.",
        "5": "Learn their preferred branch of magic.",
        "6": "Learn their hobby outside magic.",
        "7": "Hear the witch's favourite song.",
        "8": "Find their favourite novel.",
        "9": "Learn their magic sports team.",
        "10": "Find or learn about an old pet.",
        "jack": "Mistaken for the witch — favourite dish.",
        "queen": "Broken wand or staff to repair.",
        "king": "Base camps in different locales.",
    },
    "about_the_witch": {
        "ace": "Who was the witch's familiar?",
        "2": "Evidence of a strange quirk.",
        "3": "The witch's deep fear.",
        "4": "Extra time in a particular locale.",
        "5": "Someone who disliked the witch.",
        "6": "The witch's education.",
        "7": "Something they were hopelessly bad at.",
        "8": "Strange background discovery.",
        "9": "Someone who misses them deeply.",
        "10": "Something they failed to cure in time.",
        "jack": "Something the witch improved in the village.",
        "queen": "A golden opportunity they passed up.",
        "king": "Details of a family member.",
    },
}

LOCALE_META = {
    "village": {"label": "The Village", "unlock": None},
    "glimmerwood": {"label": "Glimmerwood Grove", "unlock": None, "base": True},
    "blastfire_bog": {"label": "Blastfire Bog", "unlock": "coracle"},
    "meltwater_loch": {"label": "Meltwater Loch", "unlock": None, "base": True},
    "dreamwater_depths": {"label": "Dreamwater Depths", "unlock": "bas_bata_cured"},
    "moonbreaker_mountain": {"label": "Moonbreaker Mountain", "unlock": None, "base": True},
    "cloud_isles": {"label": "The Cloud Isles", "unlock": "broom"},
    "heros_hollow": {"label": "Hero's Hollow", "unlock": None, "base": True},
    "the_strange": {"label": "The Strange", "unlock": "portal_open"},
}


def _write_yaml(name: str, data: dict, comment: str) -> None:
    path = OUT / name
    with path.open("w", encoding="utf-8") as f:
        f.write(f"# {comment}\n")
        yaml.dump(data, f, allow_unicode=True, sort_keys=False, width=120)


def _clean_reagents() -> None:
    path = OUT / "apothecaria_reagents.yaml"
    if not path.exists():
        return
    data = yaml.safe_load(path.read_text())
    raw = data.get("reagents") or []
    seen: set[str] = set()
    cleaned = []
    for reg in raw:
        name = str(reg.get("name", "")).strip()
        if not name or name in seen:
            continue
        if name in ("Reagents Explanation", "Forest Reagents", "Loch Reagents"):
            continue
        seen.add(name)
        body = str(reg.get("body", ""))
        poison = 0
        sweet = 0
        m = re.search(r"Adds?\s+(\d+)\s+points?\s+of\s+POISON", body, re.I)
        if m:
            poison = int(m.group(1))
        m = re.search(r"Adds?\s+(\d+)\s+points?\s+of\s+SWEET", body, re.I)
        if m:
            sweet = int(m.group(1))
        preps = []
        for p in ("CRUSH", "BOIL", "DISTIL", "RAW"):
            if p in body.upper():
                preps.append(p)
        tags = [t for t in (reg.get("tags") or []) if t != "TAGS"]
        entry = {
            "name": name,
            "type": reg.get("type", ""),
            "locales": reg.get("locales") or {},
            "tags": tags,
            "preparations": preps,
        }
        if poison:
            entry["poison"] = poison
        if sweet:
            entry["sweet"] = sweet
        if reg.get("requires_wand"):
            entry["requires_wand"] = True
        cleaned.append(entry)
    _write_yaml("apothecaria_reagents.yaml", {"reagents": cleaned}, "Reagents — Apothecaria p.20–29")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for loc, events in LOCALES.items():
        missing = [r for r in RANKS if r not in events]
        if missing:
            print(f"WARN {loc} missing ranks: {missing}", file=sys.stderr)
    _write_yaml("apothecaria_locale_events.yaml", {"locales": LOCALES, "meta": LOCALE_META},
                "Locale foraging events — Apothecaria p.34–51 (verified)")
    _write_yaml("apothecaria_tools.yaml", TOOLS, "Tools — Apothecaria p.6–7")
    _write_yaml("apothecaria_upgrades.yaml", {"upgrades": UPGRADES}, "Upgrades — Apothecaria p.8–9")
    _write_yaml("apothecaria_village.yaml", {"services": VILLAGE}, "Village services — Apothecaria p.32")
    _write_yaml("apothecaria_festivals.yaml", {"festivals": FESTIVALS}, "Season festivals — Apothecaria p.32–33")
    _write_yaml("apothecaria_witch_storyline.yaml", {"tables": WITCH_STORYLINE},
                "Witch mystery clues — Apothecaria p.52–54")
    _clean_reagents()
    print(f"Built locale tables: {sum(len(v) for v in LOCALES.values())} events across {len(LOCALES)} locales")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
