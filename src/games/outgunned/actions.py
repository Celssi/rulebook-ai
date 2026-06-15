"""Outgunned shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.gm_solo.dice import reroll_outgunned_pool, roll_outgunned_pool
from src.games.outgunned.curated import (
    bump_tension,
    reset_tension,
    roll_ad_prompt,
    roll_climax,
    roll_hurdle,
    roll_mission,
    roll_scene_drama,
    roll_villain_traits,
    roll_yes_no,
)
from src.play_tools import roll_dice

GAME_ID = "outgunned"

ShortcutKind = Literal["static", "rag_only", "roll", "roll_rag"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "ad_prompt", "label": "AD scene prompt", "kind": "roll_rag"},
    {"id": "mission_roll", "label": "Mission / villain roll", "kind": "roll"},
    {"id": "outgunned_roll", "label": "Outgunned dice pool", "kind": "roll"},
    {"id": "outgunned_reroll", "label": "Outgunned re-roll", "kind": "roll"},
    {"id": "death_roulette", "label": "Death Roulette", "kind": "roll"},
    {"id": "tension", "label": "Tension track", "kind": "roll"},
    {"id": "yes_no_oracle", "label": "Yes/No oracle", "kind": "roll"},
    {"id": "scene_drama", "label": "Scene drama roll", "kind": "roll"},
    {"id": "rules_help", "label": "Outgunned rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_outgunned_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if "ad prompt" in lower or "assistant director" in lower or "scene prompt" in lower:
        return "ad_prompt"
    if "mission roll" in lower or "roll mission" in lower or "villain roll" in lower:
        return "mission_roll"
    if "re-roll" in lower or "reroll" in lower or "re roll" in lower:
        return "outgunned_reroll"
    if "outgunned roll" in lower or "dice pool" in lower or "roll pool" in lower:
        return "outgunned_roll"
    if "death roulette" in lower or "spin roulette" in lower:
        return "death_roulette"
    if "tension" in lower and ("track" in lower or "scene" in lower or "shot" in lower or "end scene" in lower):
        return "tension"
    if "yes/no" in lower or "yes no oracle" in lower or "oracle roll" in lower:
        return "yes_no_oracle"
    if "scene drama" in lower:
        return "scene_drama"
    if "outgunned rules" in lower or "how to play outgunned" in lower:
        return "rules_help"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_ID,
    hero_name: str = "",
    mission_title: str = "",
    pool_dice: int = 3,
    death_roulette_bullets: int = 0,
    ad_state: dict | None = None,
    tension_action: str = "end_scene",
    yes_no_likely: bool = False,
    yes_no_unlikely: bool = False,
    free_reroll: bool = False,
) -> dict:
    _ = game_id
    state = dict(ad_state or {})
    phase = str(state.get("phase", "") or "")

    if shortcut_id == "rules_help":
        prompt = (
            "Explain Outgunned solo play with the Assistant Director supplement: "
            "Campaign phases, Solo Hero boosts, Tension, Scene Prompts, Death Roulette, "
            "matching-pair dice pools, re-rolls, and oracle tables. Cite the rulebooks."
        )
        return {"user_message": "**Outgunned rules**", "prompt": prompt, "rag_only": True}

    if shortcut_id == "ad_prompt":
        prompt_row = roll_ad_prompt()
        hurdle = roll_hurdle(variant="adventure")
        text = str(prompt_row.get("text", "") or "")
        user = (
            f"**AD prompt** ({prompt_row.get('category', 'scene')})\n\n"
            f"{text}\n\n"
            f"**Suggested hurdle:** {hurdle}\n\n"
            f"_After this Scene, bump Tension (+1, or +2 if already at 6+)._"
        )
        rag = (
            f"Outgunned solo scene. Hero {hero_name or 'unnamed'}. "
            f"Mission: {mission_title or 'unset'}. "
            f"Scene prompt: {text}. Hurdle: {hurdle}. "
            f"Suggest how to play this Scene using solo rules (Tension, Double Action)."
        )
        return {
            "user_message": user,
            "prompt": rag,
            "task": "ad_prompt",
            "ad_prompt": prompt_row,
            "hurdle": hurdle,
        }

    if shortcut_id == "mission_roll":
        mission = roll_mission()
        villain = roll_villain_traits()
        yes_no = roll_yes_no()
        title = f"{mission['type']} — {mission['complication']}"
        user = (
            f"**Mission roll**\n\n"
            f"**Type:** {mission['type']}\n"
            f"**Complication:** {mission['complication']}\n\n"
            f"**Villain:** {villain['nature']} · desires {villain['desire']} · "
            f"blocked by {villain['problem']}\n\n"
            f"**Yes/No oracle:** {yes_no['answer']} (rolled {yes_no['roll']})"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "mission_roll",
            "mission_title": title,
            "mission": mission,
            "villain": villain,
            "ad_state_patch": {
                "villain": villain,
                "mission": mission,
                "phase": state.get("phase") or "Pilot Shot",
                "tension": reset_tension(phase="Pilot Shot"),
            },
        }

    if shortcut_id == "outgunned_roll":
        dice = roll_outgunned_pool(pool_dice)
        user = f"**Outgunned roll** ({pool_dice}d6)\n\n{dice['summary']}\n\n_Re-roll available if you scored at least a Basic success._"
        rag = (
            f"Outgunned action roll for {hero_name or 'the hero'}. "
            f"{dice['summary']}. Explain success tiers and consequences using Adventure rules."
        )
        return {
            "user_message": user,
            "prompt": rag,
            "task": "outgunned_roll",
            "dice": dice,
            "roll_summary": dice["summary"],
            "ad_state_patch": {"last_pool_roll": dice},
        }

    if shortcut_id == "outgunned_reroll":
        last = state.get("last_pool_roll")
        if not isinstance(last, dict) or not last.get("rolls"):
            user = "**Re-roll:** no prior pool roll — use **Outgunned dice pool** first."
            return {"user_message": user, "prompt": user, "static": True, "task": "outgunned_reroll"}
        dice = reroll_outgunned_pool(list(last["rolls"]), free_reroll=free_reroll)
        user = f"**Outgunned re-roll**\n\n{dice.get('summary', 'Re-roll failed.')}"
        patch: dict = {}
        if dice.get("ok"):
            patch["last_pool_roll"] = dice
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "outgunned_reroll",
            "dice": dice,
            "roll_summary": dice.get("summary", ""),
            "ad_state_patch": patch,
        }

    if shortcut_id == "death_roulette":
        bullets = max(0, min(6, int(death_roulette_bullets or 0)))
        if bullets == 0:
            bullets = 1
        if bullets >= 6:
            user = "**Death Roulette:** cylinder full — Hero retires (Final Breath)."
            return {
                "user_message": user,
                "prompt": user,
                "static": True,
                "task": "death_roulette",
                "death_roulette_bullets": 6,
                "fatal": True,
            }
        roll = roll_dice("1d6")
        shot = int(roll["rolls"][0])
        hit = shot <= bullets
        if hit:
            new_bullets = bullets
            outcome = "Left for Dead — captured or removed from play (solo: I Want Them Alive)."
        else:
            new_bullets = min(6, bullets + 1)
            outcome = "Narrow escape — add a Lethal Bullet (solo Second Wind: recover 6 Grit)."
        user = (
            f"**Death Roulette** ({bullets} Lethal Bullet{'s' if bullets != 1 else ''} in cylinder)\n\n"
            f"Rolled **{shot}** — {outcome}\n\n"
            f"{roll['summary'] if 'summary' in roll else f'Rolled {shot}'}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "death_roulette",
            "death_roulette_bullets": new_bullets,
            "roll_summary": user,
            "hit": hit,
        }

    if shortcut_id == "tension":
        current = int(state.get("tension", reset_tension(phase=phase)) or 1)
        action = (tension_action or "end_scene").strip().lower()
        if action == "reset_shot":
            new_tension = reset_tension(phase=phase)
            user = f"**Tension reset** — new Shot starts at **{new_tension}/12** (phase: {phase or 'default'})."
        else:
            new_tension, delta = bump_tension(current, phase=phase)
            climax = " — **Climax now!**" if new_tension >= 12 else ""
            user = (
                f"**Tension** — end of Scene: +{delta} → **{new_tension}/12**{climax}"
            )
        patch = {"tension": new_tension}
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "tension",
            "ad_state_patch": patch,
        }

    if shortcut_id == "yes_no_oracle":
        result = roll_yes_no(likely=yes_no_likely, unlikely=yes_no_unlikely)
        odds = "likely" if yes_no_likely else "unlikely" if yes_no_unlikely else "even"
        user = (
            f"**Yes/No oracle** ({odds})\n\n"
            f"**{result['answer']}** (kept {result['roll']}, rolled {result['rolls']})\n\n"
            f"_Extreme No forces a nasty turn of fate (solo, AD s. 57)._"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "yes_no_oracle",
            "oracle": result,
        }

    if shortcut_id == "scene_drama":
        drama = roll_scene_drama()
        climax_hint = roll_climax()
        user = (
            f"**Scene Drama**\n\n"
            f"**Subject:** {drama['subject']}\n"
            f"**Sense:** {drama['sense']}\n"
            f"**Snag:** {drama['snag']}\n\n"
            f"_Climax inspiration:_ {climax_hint}"
        )
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "task": "scene_drama",
            "drama": drama,
        }

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
