"""Project paths and model settings (no game registry imports)."""

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
OCR_RENDER_DPI = 300
TESSERACT_LANG = "eng"
# LSTM engine (--oem 1), automatic page segmentation with OSD (--psm 3) — best
# default for multi-column rulebook pages.
TESSERACT_CONFIG = "--oem 1 --psm 3"

OLLAMA_BASE_URL = "http://localhost:11434"

CHAT_MODEL = os.environ.get("OLLAMA_CHAT_MODEL", "gemma4:31b")
EMBED_MODEL = "nomic-embed-text"
# nomic-embed-text is trained with task prefixes; passages and queries MUST be
# prefixed for good retrieval. Changing these requires re-indexing.
EMBED_DOCUMENT_PREFIX = "search_document: "
EMBED_QUERY_PREFIX = "search_query: "
OLLAMA_REQUEST_TIMEOUT = float(os.environ.get("OLLAMA_REQUEST_TIMEOUT", "600"))

def _load_dotenv_value(name: str) -> str | None:
    """Read a single KEY=VALUE from project-root .env if not already in os.environ."""
    if os.environ.get(name, "").strip():
        return os.environ[name].strip()
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return None
    prefix = f"{name}="
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or not stripped.startswith(prefix):
            continue
        value = stripped[len(prefix) :].strip().strip("'\"")
        if value:
            os.environ[name] = value
            return value
    return None


ANTHROPIC_API_KEY = _load_dotenv_value("ANTHROPIC_API_KEY")
CLAUDE_CHAT_MODEL = os.environ.get("CLAUDE_CHAT_MODEL", "claude-sonnet-4-6")

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
TOP_K_DEFAULT = 5

# Cross-encoder reranking (shared retrieval layer for all games)
RERANK_MODEL = os.environ.get("RERANK_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")

DEFAULT_GAME_ID = "40k"
