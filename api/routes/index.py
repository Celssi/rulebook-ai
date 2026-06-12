"""Index / ingest routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends

from api.deps import get_app_session
from src.config import OCR_CACHE_DIR, get_mvp_pdfs, get_pdf_sources
from src.games.saves import AppSession
from src.ingest import run_ingest, tyranids_codex_needs_ocr
from src.rag import index_exists

router = APIRouter(prefix="/api/index", tags=["index"])

ROOT = Path(__file__).resolve().parent.parent.parent


@router.get("/status")
def index_status(app: AppSession = Depends(get_app_session)):
    game_id = app.selected_game_id
    indexed = index_exists(game_id=game_id)
    pdf_sources = get_pdf_sources(game_id)
    mvp_pdfs = get_mvp_pdfs(game_id)
    docs = []
    for name, meta in pdf_sources.items():
        path = ROOT / "docs" / name
        docs.append(
            {
                "name": name,
                "label": meta["label"],
                "exists": path.exists(),
                "mvp": name in mvp_pdfs,
            }
        )
    ocr_warning = (
        game_id == "40k"
        and tyranids_codex_needs_ocr()
        and not (OCR_CACHE_DIR / "Codex - Tyranids (10th Edition).json").exists()
    )
    return {"indexed": indexed, "docs": docs, "ocr_warning": ocr_warning}


@router.post("/reindex")
def reindex(
    ingest_all: bool = True,
    use_ocr: bool = True,
    force_ocr: bool = False,
    app: AppSession = Depends(get_app_session),
):
    code = run_ingest(
        game_id=app.selected_game_id,
        mvp_only=not ingest_all,
        reset=True,
        use_ocr=use_ocr,
        force_ocr=force_ocr,
    )
    return {"ok": code == 0, "indexed": index_exists(game_id=app.selected_game_id)}
