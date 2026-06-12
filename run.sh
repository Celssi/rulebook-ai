#!/usr/bin/env bash
# Bootstrap and run rulebook-ai (venv, deps, Ollama, indexes, Streamlit).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 not found. Install Python 3.11+ and try again."
  exit 1
fi

if ! python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)'; then
  echo "Python 3.11+ required (found $(python3 --version))."
  exit 1
fi

BOOTSTRAP_ARGS=()
STREAMLIT_ARGS=()
PASSTHRU=false
for arg in "$@"; do
  if [[ "$arg" == "--" ]]; then
    PASSTHRU=true
    continue
  fi
  if $PASSTHRU; then
    STREAMLIT_ARGS+=("$arg")
  else
    BOOTSTRAP_ARGS+=("$arg")
  fi
done

if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies..."
pip install -q -e .

python scripts/bootstrap.py "${BOOTSTRAP_ARGS[@]}"

exec streamlit run app/streamlit_app.py "${STREAMLIT_ARGS[@]}"
