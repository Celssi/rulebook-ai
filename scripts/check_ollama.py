#!/usr/bin/env python3
"""Verify Ollama is running and required models are available."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

from src.config import CHAT_MODEL, EMBED_MODEL, OLLAMA_BASE_URL

REQUIRED = [CHAT_MODEL, EMBED_MODEL]


def _get_json(path: str) -> dict | list:
    req = urllib.request.Request(f"{OLLAMA_BASE_URL}{path}")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def main() -> int:
    try:
        tags = _get_json("/api/tags")
    except urllib.error.URLError as e:
        print(f"Ollama not reachable at {OLLAMA_BASE_URL}: {e}")
        print("Start Ollama, then run: ollama serve")
        return 1

    installed = {m.get("name", "").split(":")[0] for m in tags.get("models", [])}
    # Also match full names like llama3.2:3b
    full_names = {m.get("name", "") for m in tags.get("models", [])}

    missing = []
    for model in REQUIRED:
        base = model.split(":")[0]
        if model not in full_names and base not in installed:
            missing.append(model)

    if missing:
        print("Missing models. Pull them with:")
        for m in missing:
            print(f"  ollama pull {m}")
        return 1

    print(f"Ollama OK at {OLLAMA_BASE_URL}")
    print(f"  chat: {CHAT_MODEL}")
    print(f"  embed: {EMBED_MODEL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
