"""Game plugin registry."""

from __future__ import annotations

from src.games.base import GamePlugin
from src.games.apothecaria.plugin import PLUGIN as APOTHECARIA_PLUGIN
from src.games.ashes.plugin import PLUGIN as ASHES_PLUGIN
from src.games.brambletrek.plugin import PLUGIN as BRAMBLETREK_PLUGIN
from src.games.colostle.plugin import PLUGIN as COLOSTLE_PLUGIN
from src.games.lighthouse.plugin import PLUGIN as LIGHTHOUSE_PLUGIN
from src.games.sansibilia.plugin import PLUGIN as SANSIBILIA_PLUGIN
from src.games.whispers.plugin import PLUGIN as WHISPERS_PLUGIN
from src.games.saves import has_play_roster
from src.games.warhammer_40k.plugin import PLUGIN as WARHAMMER_40K_PLUGIN

_PLUGINS: dict[str, GamePlugin] = {
    WARHAMMER_40K_PLUGIN.game_id: WARHAMMER_40K_PLUGIN,
    BRAMBLETREK_PLUGIN.game_id: BRAMBLETREK_PLUGIN,
    SANSIBILIA_PLUGIN.game_id: SANSIBILIA_PLUGIN,
    LIGHTHOUSE_PLUGIN.game_id: LIGHTHOUSE_PLUGIN,
    APOTHECARIA_PLUGIN.game_id: APOTHECARIA_PLUGIN,
    WHISPERS_PLUGIN.game_id: WHISPERS_PLUGIN,
    COLOSTLE_PLUGIN.game_id: COLOSTLE_PLUGIN,
    ASHES_PLUGIN.game_id: ASHES_PLUGIN,
}

GAME_40K = WARHAMMER_40K_PLUGIN.game_id
GAME_BRAMBLETREK = BRAMBLETREK_PLUGIN.game_id
GAME_SANSIBILIA = SANSIBILIA_PLUGIN.game_id
GAME_LIGHTHOUSE = LIGHTHOUSE_PLUGIN.game_id
GAME_APOTHECARIA = APOTHECARIA_PLUGIN.game_id
GAME_WHISPERS = WHISPERS_PLUGIN.game_id
GAME_COLOSTLE = COLOSTLE_PLUGIN.game_id
GAME_ASHES = ASHES_PLUGIN.game_id
DEFAULT_GAME_ID = GAME_40K


def get_game_plugin(game_id: str) -> GamePlugin:
    return _PLUGINS.get(game_id, _PLUGINS[DEFAULT_GAME_ID])


def _register_play_profiles() -> None:
    from src.games.apothecaria.play import _register as register_apothecaria
    from src.games.ashes.play import _register as register_ashes
    from src.games.brambletrek.play import _register as register_brambletrek
    from src.games.colostle.play import _register as register_colostle
    from src.games.lighthouse.play import _register as register_lighthouse
    from src.games.sansibilia.play import _register as register_sansibilia
    from src.games.whispers.play import _register as register_whispers

    register_brambletrek()
    register_sansibilia()
    register_lighthouse()
    register_apothecaria()
    register_whispers()
    register_colostle()
    register_ashes()


_register_play_profiles()

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
