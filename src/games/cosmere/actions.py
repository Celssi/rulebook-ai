"""Cosmere shortcuts."""

from __future__ import annotations

from typing import Literal

from src.games.cosmere.curated import format_plot_dice_roll
from src.games.gm_solo.dice import roll_advantage_d20, roll_plot_dice

GAME_COSMERE = "cosmere"

ShortcutKind = Literal["roll", "roll_rag", "rag_only"]

SHORTCUTS: list[dict[str, str]] = [
    {"id": "plot_dice", "label": "Roll plot dice", "kind": "roll"},
    {"id": "skill_test", "label": "Skill test", "kind": "roll_rag"},
    {"id": "combat_attack", "label": "Combat attack", "kind": "roll_rag"},
    {"id": "rules_help", "label": "Cosmere rules help", "kind": "rag_only"},
]

SHORTCUT_IDS = frozenset(s["id"] for s in SHORTCUTS)


def match_cosmere_shortcut(text: str) -> str | None:
    lower = text.lower().strip()
    if "plot dice" in lower or "plot die" in lower:
        return "plot_dice"
    if "skill test" in lower or "skill check" in lower and "cosmere" in lower:
        return "skill_test"
    if "combat attack" in lower or ("attack" in lower and "cosmere" in lower):
        return "combat_attack"
    if "cosmere rules" in lower or "how to play cosmere" in lower:
        return "rules_help"
    return None


def run_shortcut(
    shortcut_id: str,
    *,
    game_id: str = GAME_COSMERE,
    plot_dice_pool: int = 0,
    path: str = "",
    role: str = "",
    expertises: list[str] | None = None,
    deflection: int = 0,
    modifier: int = 0,
    advantage: str = "normal",
    **_kwargs,
) -> dict:
    _ = game_id
    expertise_note = ""
    if expertises:
        expertise_note = f" Expertises: {', '.join(expertises)}."

    if shortcut_id == "plot_dice":
        count = max(1, min(10, int(plot_dice_pool or 1)))
        result = roll_plot_dice(count)
        detail = format_plot_dice_roll(list(result["rolls"]))
        user = f"{result['summary']}\n\n{detail}"
        return {
            "user_message": user,
            "prompt": user,
            "static": True,
            "dice": result,
            "task": "plot_dice",
        }

    if shortcut_id == "skill_test":
        adv = advantage if advantage in ("normal", "advantage", "disadvantage") else "normal"
        result = roll_advantage_d20(modifier, advantage=adv)  # type: ignore[arg-type]
        who = f"{path} / {role}".strip(" /") or "character"
        user = f"**Skill test** ({who}){expertise_note}\n\n{result['summary']}"
        prompt = (
            f"Cosmere RPG skill test for a {who}.{expertise_note} "
            f"Roll result: {result['summary']}. "
            f"Explain how to resolve success, complications, and opportunities using Stormlight rules."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "dice": result,
            "task": "skill_test",
        }

    if shortcut_id == "combat_attack":
        plot = roll_plot_dice(1)
        plot_detail = format_plot_dice_roll(list(plot["rolls"]))
        attack = roll_advantage_d20(modifier, advantage="normal")
        user = (
            f"**Combat attack**\n\n"
            f"{attack['summary']}\n\n"
            f"{plot['summary']}\n\n{plot_detail}"
        )
        if deflection:
            user += f"\n\nTarget deflection: **{deflection}**"
        prompt = (
            f"Cosmere RPG combat attack. Attack roll: {attack['summary']}. "
            f"Plot die: {plot['summary']}. "
            f"Explain hit resolution, damage, and deflection using Stormlight combat rules."
        )
        return {
            "user_message": user,
            "prompt": prompt,
            "dice": {"attack": attack, "plot": plot},
            "task": "combat_attack",
        }

    if shortcut_id == "rules_help":
        prompt = (
            "Explain how to play Cosmere RPG solo with the Stormlight Handbook: "
            "paths, roles, expertises, plot dice (complications and opportunities), "
            "skill tests, combat, and deflection. Cite the rulebooks."
        )
        return {"user_message": "**Cosmere rules**", "prompt": prompt, "rag_only": True}

    return {"user_message": "Unknown shortcut.", "prompt": "Unknown shortcut.", "static": True}
