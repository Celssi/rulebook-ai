"""Game plugin registry."""

from __future__ import annotations

from src.games.base import GamePlugin
from src.games.brambletrek import play as _brambletrek_play  # noqa: F401 — registers play profile
from src.games.brambletrek.plugin import PLUGIN as BRAMBLETREK_PLUGIN
from src.games.saves import has_play_roster
from src.games.warhammer_40k.plugin import PLUGIN as WARHAMMER_40K_PLUGIN

_PLUGINS: dict[str, GamePlugin] = {
    WARHAMMER_40K_PLUGIN.game_id: WARHAMMER_40K_PLUGIN,
    BRAMBLETREK_PLUGIN.game_id: BRAMBLETREK_PLUGIN,
}

GAME_40K = WARHAMMER_40K_PLUGIN.game_id
GAME_BRAMBLETREK = BRAMBLETREK_PLUGIN.game_id
DEFAULT_GAME_ID = GAME_40K

GAME_CATALOG: dict[str, dict] = {
    pid: {
        "label": p.label,
        "collection": p.collection,
        "pdf_sources": p.pdf_sources,
        "mvp_pdfs": p.mvp_pdfs,
        "all_factions": p.all_factions,
        "ocr_pdfs": p.ocr_pdfs,
        "has_game_state": p.has_game_state,
        "has_character_sheet": p.has_character_sheet,
        "has_play_roster": has_play_roster(pid),
    }
    for pid, p in _PLUGINS.items()
}


def get_game_plugin(game_id: str) -> GamePlugin:
    return _PLUGINS.get(game_id, _PLUGINS[DEFAULT_GAME_ID])


def get_game_config(game_id: str) -> dict:
    return GAME_CATALOG.get(game_id, GAME_CATALOG[DEFAULT_GAME_ID])


def get_collection_name(game_id: str) -> str:
    return str(get_game_config(game_id)["collection"])


def get_pdf_sources(game_id: str) -> dict[str, dict[str, str]]:
    return dict(get_game_config(game_id)["pdf_sources"])


def get_mvp_pdfs(game_id: str) -> list[str]:
    return list(get_game_config(game_id)["mvp_pdfs"])


def get_all_factions(game_id: str) -> list[str]:
    return list(get_game_config(game_id)["all_factions"])


def get_ocr_pdfs(game_id: str) -> list[str]:
    return list(get_game_config(game_id)["ocr_pdfs"])


def all_game_ids() -> list[str]:
    return list(_PLUGINS.keys())


def game_options() -> dict[str, str]:
    return {pid: p.label for pid, p in _PLUGINS.items()}
