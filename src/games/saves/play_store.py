"""Combined play roster + session + Lonelog for games with save slots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.games.saves import lonelog as lonelog_fmt
from src.games.saves.keys import session_extra_key
from src.games.saves.lonelog import LonelogStore
from src.games.saves.roster import RosterEntry, RosterStore
from src.games.saves.context import PlayContext, load_play_context_from_disk, persist_play_context
from src.games.saves.session import load_session, save_session

PlaySettingSpec = dict[str, Any]  # {"default": str, "choices": list[str]}


@dataclass
class PlayProfile:
    """Registration config for a game that uses multi-slot saves."""

    game_id: str
    game_label: str
    slot_label: str
    default_slot_name: str
    entity_from_dict: Callable[[dict | None], Any]
    entity_to_dict: Callable[[Any], dict]
    default_entity: Callable[[], Any]
    slot_display_name: Callable[[Any], str]
    lonelog_display_name: Callable[[Any], str]
    before_save_entity: Callable[[Any], None] | None = None
    entity_filename: str = "entity.json"
    has_lonelog: bool = True
    play_settings: dict[str, PlaySettingSpec] = field(default_factory=dict)
    session_extra_keys: list[str] = field(default_factory=list)


_PROFILES: dict[str, PlayProfile] = {}


def register_play_profile(profile: PlayProfile) -> None:
    _PROFILES[profile.game_id] = profile


def get_play_profile(game_id: str) -> PlayProfile | None:
    return _PROFILES.get(game_id)


def has_play_roster(game_id: str) -> bool:
    return game_id in _PROFILES


def get_play_store(game_id: str) -> PlayStore | None:
    profile = get_play_profile(game_id)
    if profile is None:
        return None
    return PlayStore(profile)


class PlayStore:
    def __init__(self, profile: PlayProfile) -> None:
        self.profile = profile
        self.roster = RosterStore(
            profile.game_id,
            entity_filename=profile.entity_filename,
            default_slot_name=profile.default_slot_name,
            entity_from_dict=profile.entity_from_dict,
            entity_to_dict=profile.entity_to_dict,
            default_entity=profile.default_entity,
            slot_display_name=profile.slot_display_name,
            before_save=profile.before_save_entity,
        )
        self.lonelog = (
            LonelogStore(profile.game_id, game_label=profile.game_label)
            if profile.has_lonelog
            else None
        )

    @property
    def game_id(self) -> str:
        return self.profile.game_id

    def list_slots(self) -> list[RosterEntry]:
        return self.roster.list_slots()

    def load_entity(self, slot_id: str) -> Any:
        return self.roster.load_entity(slot_id)

    def save_entity(self, entity: Any) -> None:
        self.roster.save_entity(entity)

    def create_slot(self, name: str = "") -> Any:
        return self.roster.create_slot(name)

    def delete_slot(self, slot_id: str) -> None:
        self.roster.delete_slot(slot_id)

    def ensure_initialized(self) -> str:
        return self.roster.ensure_initialized()

    def get_settings_ctx(self, ctx: PlayContext) -> dict[str, str]:
        out: dict[str, str] = {}
        for name, spec in self.profile.play_settings.items():
            default = str(spec.get("default", ""))
            val = ctx.settings.get(name, default)
            choices = spec.get("choices") or []
            if choices and val not in choices:
                val = default
            out[name] = val
        return out

    def lonelog_name_ctx(self, ctx: PlayContext) -> str:
        if ctx.entity is not None:
            entity = self.profile.entity_from_dict(ctx.entity)
            return self.profile.lonelog_display_name(entity)
        return self.profile.default_slot_name

    def init_ctx(self) -> PlayContext:
        slot_id = self.ensure_initialized()
        ctx = load_play_context_from_disk(self, slot_id)
        self.roster.set_active_slot_id(slot_id)
        return ctx

    def persist_ctx(self, ctx: PlayContext) -> None:
        roster_ids = {e.id for e in self.roster.list_slots()}
        if not ctx.slot_id or ctx.slot_id not in roster_ids:
            return
        persist_play_context(self, ctx)

    def switch_slot_ctx(self, ctx: PlayContext, new_slot_id: str) -> PlayContext:
        roster_ids = {e.id for e in self.roster.list_slots()}
        if ctx.slot_id and ctx.slot_id != new_slot_id and ctx.slot_id in roster_ids:
            self.persist_ctx(ctx)
        self.roster.set_active_slot_id(new_slot_id)
        return load_play_context_from_disk(self, new_slot_id)

    def _log_display(self, *, ctx: PlayContext | None = None) -> str:
        if ctx is not None:
            return self.lonelog_name_ctx(ctx)
        return self.profile.default_slot_name

    def _append_formatted(
        self, slot_id: str, line: str, *, ctx: PlayContext | None = None
    ) -> None:
        if not self.lonelog or not slot_id or not line.strip():
            return
        self.lonelog.append(slot_id, line, display_name=self._log_display(ctx=ctx))

    def log_draw(
        self,
        slot_id: str,
        cards: list[str],
        *,
        label: str = "Drew",
        st=None,
        ctx: PlayContext | None = None,
    ) -> None:
        self._append_formatted(
            slot_id, lonelog_fmt.format_draw(cards, label=label), ctx=ctx
        )

    def log_roll(
        self,
        slot_id: str,
        line: str,
        *,
        st=None,
        ctx: PlayContext | None = None,
        result: dict | None = None,
        vs: int | None = None,
        vs_label: str = "TN",
        outcome: str | None = None,
    ) -> None:
        """Append a d: mechanics line without double-prefixing."""
        if result is not None:
            formatted = lonelog_fmt.format_dice_from_result(
                result, vs=vs, vs_label=vs_label, outcome=outcome
            )
        elif line.strip().startswith("d:"):
            formatted = line.strip()
        else:
            formatted = lonelog_fmt.format_roll("", line) if "->" in line else f"d: {line.strip()}"
        self._append_formatted(slot_id, formatted, ctx=ctx)

    def log_mechanical(self, slot_id: str, text: str, *, st=None, ctx: PlayContext | None = None) -> None:
        stripped = text.strip()
        if stripped.startswith("d:"):
            self._append_formatted(slot_id, stripped, ctx=ctx)
            return
        self._append_formatted(slot_id, lonelog_fmt.format_mechanical(text), ctx=ctx)

    def log_resolution(self, slot_id: str, text: str, *, st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_resolution(text), ctx=ctx)

    def log_oracle_question(self, slot_id: str, text: str, *, st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_oracle_question(text), ctx=ctx)

    def log_narrative(self, slot_id: str, text: str, *, st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_narrative(text), ctx=ctx)

    def log_player_action(self, slot_id: str, text: str, *, actor: str = "", st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(
            slot_id, lonelog_fmt.format_player_action(text, actor=actor), ctx=ctx
        )

    def log_table(
        self,
        slot_id: str,
        table: str,
        result: str,
        *,
        roll: str = "",
        options: list[str] | None = None,
        st=None,
        ctx: PlayContext | None = None,
    ) -> None:
        self._append_formatted(
            slot_id,
            lonelog_fmt.format_table(table, result, roll=roll, options=options),
            ctx=ctx,
        )

    def log_generator(
        self,
        slot_id: str,
        name: str,
        result: str,
        *,
        axes: dict[str, str] | None = None,
        st=None,
        ctx: PlayContext | None = None,
    ) -> None:
        self._append_formatted(
            slot_id, lonelog_fmt.format_generator(name, result, axes=axes), ctx=ctx
        )

    def log_meta(self, slot_id: str, text: str, *, kind: str = "note", st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_meta_note(text, kind=kind), ctx=ctx)

    def log_scene(
        self,
        slot_id: str,
        scene_id: str | int,
        context: str = "",
        *,
        st=None,
        ctx: PlayContext | None = None,
        **kwargs: Any,
    ) -> None:
        if not self.lonelog or not slot_id:
            return
        self.lonelog.append_scene(
            slot_id,
            scene_id,
            context,
            display_name=self._log_display(ctx=ctx),
            **kwargs,
        )

    def log_tag(self, slot_id: str, tag_line: str, *, st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(slot_id, tag_line.strip(), ctx=ctx)

    def log_block(
        self,
        slot_id: str,
        block_name: str,
        lines: list[str],
        *,
        st=None,
        ctx: PlayContext | None = None,
    ) -> None:
        if not self.lonelog or not slot_id:
            return
        self.lonelog.append_block(
            slot_id, block_name, lines, display_name=self._log_display(ctx=ctx)
        )

    def append_log(self, slot_id: str, line: str, *, st=None, ctx: PlayContext | None = None) -> None:
        self._append_formatted(slot_id, line, ctx=ctx)

    def recent_log_context(self, slot_id: str, n_lines: int = 40) -> str:
        if not self.lonelog or not slot_id:
            return ""
        return self.lonelog.recent_context(slot_id, n_lines=n_lines)

    def read_log_tail(self, slot_id: str, n_lines: int = 30) -> list[str]:
        if not self.lonelog or not slot_id:
            return []
        return self.lonelog.read_tail(slot_id, n_lines=n_lines)

    def log_path(self, slot_id: str):
        if not self.lonelog:
            raise RuntimeError("Lonelog not enabled for this game")
        return self.lonelog.path(slot_id)
