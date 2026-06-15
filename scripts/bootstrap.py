#!/usr/bin/env python3
"""Bootstrap rulebook-ai: Ollama, models, indexes, smoke checks."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import (  # noqa: E402
    CHAT_MODEL,
    DOCS_DIR,
    EMBED_MODEL,
    GAME_CATALOG,
    OLLAMA_BASE_URL,
    get_mvp_pdfs,
)
from src.ingest import run_ingest  # noqa: E402
from src.rag import index_exists  # noqa: E402

REQUIRED_MODELS = [CHAT_MODEL, EMBED_MODEL]
OLLAMA_RETRY_SECONDS = 30
OLLAMA_RETRY_INTERVAL = 2


def _get_json(path: str) -> dict | list:
    req = urllib.request.Request(f"{OLLAMA_BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def ollama_reachable() -> bool:
    try:
        _get_json("/api/tags")
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _try_start_ollama_macos() -> None:
    if platform.system() != "Darwin":
        return
    print("Starting Ollama app (macOS)...")
    subprocess.run(["open", "-a", "Ollama"], check=False)


def ensure_ollama_running(*, skip: bool = False) -> bool:
    if ollama_reachable():
        print(f"Ollama OK at {OLLAMA_BASE_URL}")
        return True

    if skip:
        print(f"WARNING: Ollama not reachable at {OLLAMA_BASE_URL} (--skip-ollama)")
        return False

    print(f"Ollama not reachable at {OLLAMA_BASE_URL}")
    _try_start_ollama_macos()
    deadline = time.monotonic() + OLLAMA_RETRY_SECONDS
    while time.monotonic() < deadline:
        if ollama_reachable():
            print(f"Ollama OK at {OLLAMA_BASE_URL}")
            return True
        time.sleep(OLLAMA_RETRY_INTERVAL)

    print("Ollama still not reachable. Start it manually, then re-run ./run.sh")
    print("  macOS: open -a Ollama")
    print("  CLI:   ollama serve")
    return False


def missing_models() -> list[str]:
    try:
        tags = _get_json("/api/tags")
    except (urllib.error.URLError, TimeoutError, OSError):
        return list(REQUIRED_MODELS)

    installed = {m.get("name", "").split(":")[0] for m in tags.get("models", [])}
    full_names = {m.get("name", "") for m in tags.get("models", [])}

    missing: list[str] = []
    for model in REQUIRED_MODELS:
        base = model.split(":")[0]
        if model not in full_names and base not in installed:
            missing.append(model)
    return missing


def pull_models(*, skip: bool = False) -> bool:
    missing = missing_models()
    if not missing:
        print(f"  chat: {CHAT_MODEL}")
        print(f"  embed: {EMBED_MODEL}")
        return True

    if skip:
        print("WARNING: missing Ollama models (--skip-ollama):")
        for model in missing:
            print(f"  ollama pull {model}")
        return False

    for model in missing:
        print(f"Pulling {model}...")
        result = subprocess.run(["ollama", "pull", model], check=False)
        if result.returncode != 0:
            print(f"Failed to pull {model}")
            return False

    still_missing = missing_models()
    if still_missing:
        print("Models still missing after pull:", ", ".join(still_missing))
        return False

    print(f"  chat: {CHAT_MODEL}")
    print(f"  embed: {EMBED_MODEL}")
    return True


def _mvp_pdfs_present(game_id: str) -> list[Path]:
    present: list[Path] = []
    for name in get_mvp_pdfs(game_id):
        path = DOCS_DIR / name
        if path.is_file():
            present.append(path)
    return present


def ensure_indexes(*, skip: bool = False, ingest_all: bool = False) -> bool:
    if skip:
        print("Skipping index build (--skip-ingest)")
        return True

    mvp_only = not ingest_all
    ok = True

    for game_id in GAME_CATALOG:
        label = GAME_CATALOG[game_id]["label"]
        pdfs = _mvp_pdfs_present(game_id)
        if not pdfs:
            print(f"  {label}: no MVP PDFs in docs/ — skipping ingest")
            continue

        if index_exists(game_id):
            print(f"  {label}: index ready")
            continue

        scope = "MVP" if mvp_only else "full"
        print(f"  {label}: building {scope} index ({len(pdfs)} PDF(s))...")
        code = run_ingest(game_id, mvp_only=mvp_only, reset=True, use_ocr=True)
        if code != 0:
            print(f"  {label}: ingest failed (exit {code})")
            ok = False
        else:
            print(f"  {label}: index ready")

    return ok


def run_checks(*, skip: bool = False) -> bool:
    if skip:
        print("Skipping smoke checks (--skip-checks)")
        return True

    scripts = [
        ROOT / "scripts" / "validate_play_tools.py",
        ROOT / "scripts" / "validate_how_to_play.py",
        ROOT / "scripts" / "validate_brambletrek_lonelog.py",
    ]
    ok = True
    for script in scripts:
        print(f"Running {script.name}...")
        result = subprocess.run([sys.executable, str(script)], cwd=ROOT, check=False)
        if result.returncode != 0:
            print(f"  FAILED: {script.name}")
            ok = False

    curated = ROOT / "scripts" / "validate_brambletrek_curated.py"
    if curated.is_file():
        print(f"Running {curated.name}...")
        result = subprocess.run([sys.executable, str(curated)], cwd=ROOT, check=False)
        if result.returncode != 0:
            print(f"  WARNING: {curated.name} failed (Brambletrek PDFs/YAML may be incomplete)")

    return ok


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap rulebook-ai before starting Streamlit")
    parser.add_argument("--skip-ollama", action="store_true", help="Do not start Ollama or pull models")
    parser.add_argument("--skip-ingest", action="store_true", help="Do not build missing vector indexes")
    parser.add_argument("--skip-checks", action="store_true", help="Skip validation scripts")
    parser.add_argument(
        "--ingest-all",
        action="store_true",
        help="Build full indexes (not MVP-only) when ingest is needed",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    skip_ollama = args.skip_ollama

    print("=== Ollama ===")
    if not ensure_ollama_running(skip=skip_ollama):
        if not skip_ollama:
            return 1
    elif not pull_models(skip=skip_ollama):
        if not skip_ollama:
            return 1

    print("=== Indexes ===")
    if not ensure_indexes(skip=args.skip_ingest, ingest_all=args.ingest_all):
        return 1

    print("=== Smoke checks ===")
    if not run_checks(skip=args.skip_checks):
        return 1

    print("Bootstrap complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
