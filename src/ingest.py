"""Ingest PDFs from docs/ into Chroma via LlamaIndex + Ollama embeddings."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import chromadb
from llama_index.core import Document, StorageContext, VectorStoreIndex
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from pypdf import PdfReader

from src.config import (
    CHROMA_DIR,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    DEFAULT_GAME_ID,
    DOCS_DIR,
    EMBED_DOCUMENT_PREFIX,
    EMBED_MODEL,
    EMBED_QUERY_PREFIX,
    GAME_CATALOG,
    OLLAMA_BASE_URL,
    get_collection_name,
    get_mvp_pdfs,
    get_ocr_pdfs,
    get_pdf_sources,
)
from src.ocr import (
    OcrNotAvailableError,
    extract_pages_with_ocr,
    needs_ocr,
    ocr_pdf_page_indices,
)
from src.text_utils import clean_text, is_low_quality, is_meaningful


def _keep_chunk(text: str) -> bool:
    if is_meaningful(text, min_chars=25, min_alpha_ratio=0.12):
        return True
    compact = re.sub(r"\s+", "", text)
    has_letters = bool(re.search(r"[A-Za-z]{3,}", text))
    has_numbers = bool(re.search(r"\d", text))
    return len(compact) >= 20 and has_letters and has_numbers


def _hard_split(text: str, chunk_size: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def _split_long_paragraph(paragraph: str, chunk_size: int) -> list[str]:
    if len(paragraph) <= chunk_size:
        return [paragraph]
    sentence_parts = re.split(r"(?<=[.!?])\s+", paragraph)
    if len(sentence_parts) <= 1:
        return _hard_split(paragraph, chunk_size)
    out: list[str] = []
    buf: list[str] = []
    buf_len = 0
    for sent in sentence_parts:
        sent = sent.strip()
        if not sent:
            continue
        if len(sent) > chunk_size:
            if buf:
                out.append(" ".join(buf))
                buf = []
                buf_len = 0
            out.extend(_hard_split(sent, chunk_size))
            continue
        add_len = len(sent) + (1 if buf else 0)
        if buf and buf_len + add_len > chunk_size:
            out.append(" ".join(buf))
            buf = [sent]
            buf_len = len(sent)
        else:
            buf.append(sent)
            buf_len += add_len
    if buf:
        joined = " ".join(buf)
        if len(joined) > chunk_size:
            out.extend(_hard_split(joined, chunk_size))
        else:
            out.append(joined)
    return out


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text] if _keep_chunk(text) else []

    paragraphs = [p.strip() for p in re.split(r"\n{2,}", text) if p.strip()]
    expanded: list[str] = []
    for para in paragraphs:
        expanded.extend(_split_long_paragraph(para, chunk_size))

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for part in expanded:
        add_len = len(part) + (2 if current else 0)
        if current and current_len + add_len > chunk_size:
            chunks.append("\n\n".join(current).strip())
            if overlap > 0:
                tail = chunks[-1][-overlap:].strip()
                current = [tail, part] if tail else [part]
                current_len = len("\n\n".join(current))
            else:
                current = [part]
                current_len = len(part)
            continue
        current.append(part)
        current_len += add_len
    if current:
        chunks.append("\n\n".join(current).strip())

    capped: list[str] = []
    for chunk in chunks:
        capped.extend(_hard_split(chunk, chunk_size))
    return [c for c in capped if _keep_chunk(c)]


def extract_pages_pypdf(pdf_path: Path) -> list[tuple[int, str]]:
    reader = PdfReader(str(pdf_path))
    pages: list[tuple[int, str]] = []
    for i, page in enumerate(reader.pages):
        raw = page.extract_text() or ""
        cleaned = clean_text(raw)
        if cleaned:
            pages.append((i + 1, cleaned))
    return pages


def extract_pages(
    pdf_path: Path,
    use_ocr: bool = True,
    force_ocr: bool = False,
    ocr_pdfs: list[str] | None = None,
) -> tuple[list[tuple[int, str, str]], str]:
    """Return (pages, extraction_method). extraction_method: pypdf | ocr | hybrid | none."""
    pypdf_pages = extract_pages_pypdf(pdf_path)
    page_map: dict[int, str] = {page_num: txt for page_num, txt in pypdf_pages if txt}
    methods: dict[int, str] = {page_num: "pypdf" for page_num, _ in pypdf_pages if page_num in page_map}

    ocr_pdfs = ocr_pdfs or []
    should_ocr_doc = use_ocr and (
        force_ocr or needs_ocr(pdf_path) or pdf_path.name in ocr_pdfs
    )

    if use_ocr:
        try:
            if force_ocr or (should_ocr_doc and not page_map):
                ocr_pages = extract_pages_with_ocr(pdf_path, force=force_ocr)
                page_map = {page_num: txt for page_num, txt in ocr_pages if txt}
                methods = {page_num: "ocr" for page_num in page_map}
            else:
                total_pages = len(PdfReader(str(pdf_path)).pages)
                weak_pages = [
                    page_num
                    for page_num, text in page_map.items()
                    if is_low_quality(text, min_chars=60, min_alpha_ratio=0.2)
                ]
                missing_pages = [p for p in range(1, total_pages + 1) if p not in page_map]
                target_pages = sorted(set(weak_pages + missing_pages))
                # OCR missing pages too, not only weak extracted pages. This
                # helps capture image/table-heavy pages (e.g. prompt tables).
                if target_pages and (should_ocr_doc or bool(weak_pages) or bool(missing_pages)):
                    ocr_pages = ocr_pdf_page_indices(pdf_path, target_pages)
                    for page_num, ocr_text in ocr_pages:
                        base = page_map.get(page_num, "")
                        prefer_ocr = (
                            not base
                            or is_low_quality(base, min_chars=60, min_alpha_ratio=0.2)
                            or len(ocr_text) > int(len(base) * 1.2)
                        )
                        if prefer_ocr:
                            page_map[page_num] = ocr_text
                            methods[page_num] = "ocr"
        except OcrNotAvailableError as e:
            print(f"    OCR ERROR: {e}")

    pages = [
        (p, t, methods.get(p, "pypdf"))
        for p, t in sorted(page_map.items())
        if t and len(t.strip()) >= 10
    ]
    if not pages:
        return [], "none"

    method_values = set(method for _, _, method in pages)
    if method_values == {"ocr"}:
        extraction = "ocr"
    elif method_values == {"pypdf"}:
        extraction = "pypdf"
    else:
        extraction = "hybrid"
    return pages, extraction


def tyranids_codex_needs_ocr() -> bool:
    path = DOCS_DIR / "40k/Codex - Tyranids (10th Edition).pdf"
    return path.exists() and needs_ocr(path)


def build_documents(
    pdf_path: Path,
    meta: dict[str, str],
    use_ocr: bool = True,
    force_ocr: bool = False,
    ocr_pdfs: list[str] | None = None,
) -> list[Document]:
    pages, extraction = extract_pages(
        pdf_path,
        use_ocr=use_ocr,
        force_ocr=force_ocr,
        ocr_pdfs=ocr_pdfs,
    )
    docs: list[Document] = []
    source_file = pdf_path.name
    for page_num, page_text, page_extraction in pages:
        for chunk in _chunk_text(page_text, CHUNK_SIZE, CHUNK_OVERLAP):
            chunk_meta = {
                "source_file": source_file,
                "source_label": meta["label"],
                "page": str(page_num),
                "faction": meta["faction"],
                "extraction": extraction,
                "page_extraction": page_extraction,
            }
            docs.append(Document(text=chunk, metadata=chunk_meta))
    return docs


def load_pdf_list(
    game_id: str,
    mvp_only: bool,
    ocr_only: bool = False,
) -> list[str]:
    ocr_pdfs = get_ocr_pdfs(game_id)
    mvp_pdfs = get_mvp_pdfs(game_id)
    pdf_sources = get_pdf_sources(game_id)
    if ocr_only:
        return [n for n in ocr_pdfs if (DOCS_DIR / n).exists()]
    if mvp_only:
        return list(mvp_pdfs)
    return list(pdf_sources.keys())


def run_ingest(
    game_id: str = DEFAULT_GAME_ID,
    mvp_only: bool = True,
    reset: bool = True,
    use_ocr: bool = True,
    force_ocr: bool = False,
    ocr_only: bool = False,
) -> int:
    pdf_sources = get_pdf_sources(game_id)
    ocr_pdfs = get_ocr_pdfs(game_id)
    collection_name = get_collection_name(game_id)
    pdf_names = load_pdf_list(game_id, mvp_only, ocr_only=ocr_only)
    all_docs: list[Document] = []

    for name in pdf_names:
        path = DOCS_DIR / name
        if not path.exists():
            print(f"SKIP (missing): {name}")
            continue
        meta = pdf_sources.get(name, {"faction": "core", "label": name})
        page_docs = build_documents(
            path,
            meta,
            use_ocr=use_ocr,
            force_ocr=force_ocr,
            ocr_pdfs=ocr_pdfs,
        )
        print(f"  {name}: {len(page_docs)} chunks")
        if len(page_docs) == 0:
            print(
                f"    WARNING: no text extracted from {name}. "
                "It may be image-only — install Tesseract (brew install tesseract) "
                "and re-run with --ocr."
            )
        all_docs.extend(page_docs)

    if ocr_only:
        if not all_docs:
            print("OCR produced no chunks.")
            return 1
        print(f"OCR-only: {len(all_docs)} chunks (not embedding; use full ingest).")
        return 0

    if not all_docs:
        print("No documents to index. Add PDFs to docs/ folder.")
        return 1

    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    embed_model = OllamaEmbedding(
        model_name=EMBED_MODEL,
        base_url=OLLAMA_BASE_URL,
        text_instruction=EMBED_DOCUMENT_PREFIX,
        query_instruction=EMBED_QUERY_PREFIX,
    )

    print(f"Embedding {len(all_docs)} chunks with {EMBED_MODEL}...")
    VectorStoreIndex.from_documents(
        all_docs,
        storage_context=storage_context,
        embed_model=embed_model,
        show_progress=True,
    )
    print(f"Done. Index '{collection_name}' stored in {CHROMA_DIR}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Index Warhammer 40k PDFs into Chroma")
    parser.add_argument(
        "--game",
        choices=list(GAME_CATALOG.keys()),
        default=DEFAULT_GAME_ID,
        help="Game dataset to index (40k or brambletrek).",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include codex PDFs (slower, larger index)",
    )
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Append without deleting existing collection",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Force OCR refresh (ignore cache) for image PDFs",
    )
    parser.add_argument(
        "--no-ocr",
        action="store_true",
        help="Disable OCR fallback for image-only PDFs",
    )
    parser.add_argument(
        "--ocr-only",
        action="store_true",
        help="Run OCR on image PDFs only (build cache, no embedding)",
    )
    args = parser.parse_args()
    mvp_only = not args.all and not args.ocr_only
    label = "OCR-only" if args.ocr_only else ("MVP" if mvp_only else "full")
    print(f"Ingest game={args.game} ({label}) from {DOCS_DIR}")
    sys.exit(
        run_ingest(
            game_id=args.game,
            mvp_only=mvp_only,
            reset=not args.no_reset and not args.ocr_only,
            use_ocr=not args.no_ocr,
            force_ocr=args.ocr,
            ocr_only=args.ocr_only,
        )
    )


if __name__ == "__main__":
    main()
