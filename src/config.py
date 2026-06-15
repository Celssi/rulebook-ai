"""Project configuration: settings plus game registry."""

from src.settings import *  # noqa: F403
from src.games.registry import (  # noqa: E402
    DEFAULT_GAME_ID,
    GAME_40K,
    GAME_BRAMBLETREK,
    GAME_SANSIBILIA,
    GAME_LIGHTHOUSE,
    GAME_APOTHECARIA,
    GAME_WHISPERS,
    GAME_COLOSTLE,
    GAME_ASHES,
    GAME_CATALOG,
    get_all_factions,
    get_collection_name,
    get_game_config,
    get_mvp_pdfs,
    get_ocr_pdfs,
    get_pdf_sources,
)
