#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m pytest tests/ -q
python3 scripts/validate_play_tools.py
python3 scripts/validate_shortcuts.py
