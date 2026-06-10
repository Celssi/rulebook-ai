"""Project paths and model settings."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
DATA_DIR = ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma"
CURATED_DIR = DATA_DIR / "curated"
LEVIATHAN_YAML = CURATED_DIR / "leviathan_units.yaml"
OCR_CACHE_DIR = DATA_DIR / "ocr_cache"

OCR_MIN_CHARS_SAMPLE = 200
OCR_RENDER_DPI = 200
TESSERACT_LANG = "eng"

OLLAMA_BASE_URL = "http://localhost:11434"

# Chat model (Ollama). See https://ollama.com/library/qwen3.6
# Override: export OLLAMA_CHAT_MODEL=qwen2.5:7b (works on older Ollama)
CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "qwen3.6:35b")
EMBED_MODEL = "nomic-embed-text"
# Increase for slower models/hardware. Override with env var if needed.
OLLAMA_REQUEST_TIMEOUT = float(os.environ.get("OLLAMA_REQUEST_TIMEOUT", "600"))

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
TOP_K_DEFAULT = 5

GAME_40K = "40k"
GAME_BRAMBLETREK = "brambletrek"
DEFAULT_GAME_ID = GAME_40K

# 40k sources
PDF_SOURCES_40K: dict[str, dict[str, str]] = {
    "40k/Warhammer-40k-Quickstart-Guide.pdf": {
        "faction": "core",
        "label": "Quickstart Guide",
    },
    "40k/Warhammer-40k-Core-Rules.pdf": {
        "faction": "core",
        "label": "Core Rules",
    },
    "40k/Adeptus Astartes Cards.pdf": {
        "faction": "cards_sm",
        "label": "Space Marines Cards",
    },
    "40k/Tyranid Cards.pdf": {
        "faction": "cards_nids",
        "label": "Tyranid Cards",
    },
    "40k/Codex - Space Marines (10th Edition).pdf": {
        "faction": "space_marines",
        "label": "Codex Space Marines",
    },
    "40k/Codex - Tyranids (10th Edition).pdf": {
        "faction": "tyranids",
        "label": "Codex Tyranids",
    },
}

# 40k MVP subset (codexes added via --all flag or default full ingest)
MVP_PDFS_40K = [
    "40k/Warhammer-40k-Quickstart-Guide.pdf",
    "40k/Warhammer-40k-Core-Rules.pdf",
    "40k/Adeptus Astartes Cards.pdf",
    "40k/Tyranid Cards.pdf",
]

ALL_FACTIONS_40K = ["core", "space_marines", "tyranids", "cards_sm", "cards_nids"]

# 40k PDFs known to be image-only; OCR attempted when text extraction fails
OCR_PDFS_40K = [
    "40k/Codex - Tyranids (10th Edition).pdf",
]

# Brambletrek sources — index Complete Digital Edition only (includes core rules +
# Secrets of the World Tree, Dungeons of Dragonkeep, Pumpkin Party, First Frost).
# Separate PDFs kept only where NOT in the bundle: Birthday of Wonders, Winter Gift.
PDF_SOURCES_BRAMBLETREK: dict[str, dict[str, str]] = {
    "brambletrek/Brambletrek_-_Complete_Digital_Edition.pdf": {
        "faction": "core",
        "label": "Brambletrek Complete Digital Edition",
    },
    "brambletrek/Brambletrek_-_A_Birthday_of_Wonders.pdf": {
        "faction": "adventure",
        "label": "Brambletrek: A Birthday of Wonders",
    },
    "brambletrek/Brambletrek_-_Winter_Gift.pdf": {
        "faction": "adventure",
        "label": "Brambletrek: Winter Gift",
    },
}

MVP_PDFS_BRAMBLETREK = [
    "brambletrek/Brambletrek_-_Complete_Digital_Edition.pdf",
]

ALL_FACTIONS_BRAMBLETREK = ["core", "adventure"]

GAME_CATALOG: dict[str, dict] = {
    GAME_40K: {
        "label": "Warhammer 40,000",
        "collection": "40k_rules",
        "pdf_sources": PDF_SOURCES_40K,
        "mvp_pdfs": MVP_PDFS_40K,
        "all_factions": ALL_FACTIONS_40K,
        "ocr_pdfs": OCR_PDFS_40K,
        "has_game_state": True,
    },
    GAME_BRAMBLETREK: {
        "label": "Brambletrek",
        "collection": "brambletrek_rules",
        "pdf_sources": PDF_SOURCES_BRAMBLETREK,
        "mvp_pdfs": MVP_PDFS_BRAMBLETREK,
        "all_factions": ALL_FACTIONS_BRAMBLETREK,
        "ocr_pdfs": [],
        "has_game_state": False,
        "has_character_sheet": True,
    },
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


# Backward-compatible 40k defaults used by existing call sites.
CHROMA_COLLECTION = get_collection_name(DEFAULT_GAME_ID)
PDF_SOURCES = get_pdf_sources(DEFAULT_GAME_ID)
MVP_PDFS = get_mvp_pdfs(DEFAULT_GAME_ID)
ALL_FACTIONS = get_all_factions(DEFAULT_GAME_ID)
OCR_PDFS = get_ocr_pdfs(DEFAULT_GAME_ID)
