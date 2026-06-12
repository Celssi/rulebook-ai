"""Combined play roster + session + Lonelog for games with save slots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from src.games.saves import lonelog as lonelog_fmt
from src.games.saves.keys import (
    active_slot_key,
    play_setting_key,
    session_extra_key,
    slot_entity_key,
)
from src.games.saves.lonelog import LonelogStore
from src.games.saves.roster import RosterEntry, RosterStore
from src.games.saves.session import PlaySession, load_session, save_session
from src.play_tools import deck_scope_key, sync_deck_store

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

    def active_slot_id(self, st) -> str:
        key = active_slot_key(self.game_id)
        return st.session_state.get(key) or self.roster.get_active_slot_id() or ""

    def get_settings(self, st) -> dict[str, str]:
        out: dict[str, str] = {}
        for name, spec in self.profile.play_settings.items():
            default = str(spec.get("default", ""))
            val = st.session_state.get(play_setting_key(self.game_id, name), default)
            choices = spec.get("choices") or []
            if choices and val not in choices:
                val = default
            out[name] = val
        return out

    def get_extra(self, st, name: str) -> Any:
        return st.session_state.get(session_extra_key(self.game_id, name))

    def set_extra(self, st, name: str, value: Any) -> None:
        st.session_state[session_extra_key(self.game_id, name)] = value

    def session_from_streamlit(self, st) -> PlaySession:
        from app.components.shared import deck_key

        slot_id = self.active_slot_id(st)
        deck = st.session_state.get(deck_key(self.game_id, slot_id or None))
        settings = self.get_settings(st)
        extra = {
            key: st.session_state.get(session_extra_key(self.game_id, key))
            for key in self.profile.session_extra_keys
        }
        return PlaySession(
            deck=deck,
            messages=list(st.session_state.get("messages") or []),
            settings=settings,
            extra=extra,
        )

    def apply_session_to_streamlit(self, st, slot_id: str, session: PlaySession) -> None:
        from app.components.shared import deck_key

        st.session_state[active_slot_key(self.game_id)] = slot_id
        st.session_state.messages = list(session.messages)
        for name, spec in self.profile.play_settings.items():
            st.session_state[play_setting_key(self.game_id, name)] = session.settings.get(
                name, spec.get("default", "")
            )
        for key in self.profile.session_extra_keys:
            st.session_state[session_extra_key(self.game_id, key)] = session.extra.get(key)
        deck_k = deck_key(self.game_id, slot_id)
        st.session_state[deck_k] = session.deck
        sync_deck_store(deck_scope_key(self.game_id, slot_id), session.deck)

    def persist(self, st) -> None:
        slot_id = self.active_slot_id(st)
        if not slot_id:
            return
        entity_key = slot_entity_key(self.game_id)
        if entity_key in st.session_state:
            raw = st.session_state[entity_key]
            entity = self.profile.entity_from_dict(raw)
            if isinstance(entity, dict):
                entity["id"] = slot_id
            elif hasattr(entity, "id"):
                entity.id = slot_id
            self.save_entity(entity)
        save_session(self.game_id, slot_id, self.session_from_streamlit(st))

    def switch_slot(self, st, new_slot_id: str) -> None:
        current_id = self.active_slot_id(st)
        if current_id and current_id != new_slot_id:
            self.persist(st)

        self.roster.set_active_slot_id(new_slot_id)
        entity = self.load_entity(new_slot_id)
        session = load_session(self.game_id, new_slot_id)

        st.session_state[slot_entity_key(self.game_id)] = self.profile.entity_to_dict(entity)
        self.apply_session_to_streamlit(st, new_slot_id, session)

    def init_streamlit(self, st) -> None:
        slot_id = self.ensure_initialized()
        if self.active_slot_id(st) != slot_id:
            self.switch_slot(st, slot_id)
            return

        entity_key = slot_entity_key(self.game_id)
        if entity_key not in st.session_state:
            entity = self.load_entity(slot_id)
            st.session_state[entity_key] = self.profile.entity_to_dict(entity)

        if not self.profile.play_settings:
            return
        probe = play_setting_key(self.game_id, next(iter(self.profile.play_settings)))
        if probe not in st.session_state:
            session = load_session(self.game_id, slot_id)
            self.apply_session_to_streamlit(st, slot_id, session)

    def lonelog_name(self, st) -> str:
        entity_key = slot_entity_key(self.game_id)
        if entity_key in st.session_state:
            entity = self.profile.entity_from_dict(st.session_state[entity_key])
            return self.profile.lonelog_display_name(entity)
        return self.profile.default_slot_name

    def _log_display(self, st) -> str:
        return self.lonelog_name(st) if st is not None else self.profile.default_slot_name

    def _append_formatted(self, slot_id: str, line: str, *, st=None) -> None:
        if not self.lonelog or not slot_id or not line.strip():
            return
        self.lonelog.append(slot_id, line, display_name=self._log_display(st))

    def log_draw(
        self,
        slot_id: str,
        cards: list[str],
        *,
        label: str = "Drew",
        st=None,
    ) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_draw(cards, label=label), st=st)

    def log_roll(
        self,
        slot_id: str,
        line: str,
        *,
        st=None,
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
        self._append_formatted(slot_id, formatted, st=st)

    def log_mechanical(self, slot_id: str, text: str, *, st=None) -> None:
        stripped = text.strip()
        if stripped.startswith("d:"):
            self._append_formatted(slot_id, stripped, st=st)
            return
        self._append_formatted(slot_id, lonelog_fmt.format_mechanical(text), st=st)

    def log_resolution(self, slot_id: str, text: str, *, st=None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_resolution(text), st=st)

    def log_oracle_question(self, slot_id: str, text: str, *, st=None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_oracle_question(text), st=st)

    def log_narrative(self, slot_id: str, text: str, *, st=None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_narrative(text), st=st)

    def log_player_action(self, slot_id: str, text: str, *, actor: str = "", st=None) -> None:
        self._append_formatted(
            slot_id, lonelog_fmt.format_player_action(text, actor=actor), st=st
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
    ) -> None:
        self._append_formatted(
            slot_id,
            lonelog_fmt.format_table(table, result, roll=roll, options=options),
            st=st,
        )

    def log_generator(
        self,
        slot_id: str,
        name: str,
        result: str,
        *,
        axes: dict[str, str] | None = None,
        st=None,
    ) -> None:
        self._append_formatted(
            slot_id, lonelog_fmt.format_generator(name, result, axes=axes), st=st
        )

    def log_meta(self, slot_id: str, text: str, *, kind: str = "note", st=None) -> None:
        self._append_formatted(slot_id, lonelog_fmt.format_meta_note(text, kind=kind), st=st)

    def log_scene(
        self,
        slot_id: str,
        scene_id: str | int,
        context: str = "",
        *,
        st=None,
        **kwargs: Any,
    ) -> None:
        if not self.lonelog or not slot_id:
            return
        self.lonelog.append_scene(
            slot_id,
            scene_id,
            context,
            display_name=self._log_display(st),
            **kwargs,
        )

    def log_tag(self, slot_id: str, tag_line: str, *, st=None) -> None:
        self._append_formatted(slot_id, tag_line.strip(), st=st)

    def log_block(
        self,
        slot_id: str,
        block_name: str,
        lines: list[str],
        *,
        st=None,
    ) -> None:
        if not self.lonelog or not slot_id:
            return
        self.lonelog.append_block(
            slot_id, block_name, lines, display_name=self._log_display(st)
        )

    def append_log(self, slot_id: str, line: str, *, st=None) -> None:
        self._append_formatted(slot_id, line, st=st)

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
