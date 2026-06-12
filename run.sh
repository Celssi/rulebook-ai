#!/usr/bin/env bash
# Bootstrap and run rulebook-ai (venv, deps, Ollama, indexes, API + React UI).
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
API_ARGS=()
UI_MODE="react"
PASSTHRU=false
for arg in "$@"; do
  if [[ "$arg" == "--" ]]; then
    PASSTHRU=true
    continue
  fi
  if $PASSTHRU; then
    API_ARGS+=("$arg")
  else
    BOOTSTRAP_ARGS+=("$arg")
  fi
done

ensure_venv() {
  if [[ -d .venv && -f .venv/bin/pip ]]; then
    pip_interp="$(head -1 .venv/bin/pip | sed 's/^#!//' | tr -d '[:space:]')"
    if [[ -n "$pip_interp" && ! -x "$pip_interp" ]]; then
      echo "Removing virtual environment (scripts point at missing Python: $pip_interp)..."
      rm -rf .venv
    fi
  fi
  if [[ -d .venv && -f .venv/pyvenv.cfg ]]; then
    venv_cmd="$(grep '^command = ' .venv/pyvenv.cfg 2>/dev/null || true)"
    venv_dest="${venv_cmd##* venv }"
    if [[ -n "$venv_dest" && "$venv_dest" != "$ROOT/.venv" ]]; then
      echo "Removing virtual environment from a previous project path..."
      rm -rf .venv
    fi
  fi
  if [[ -d .venv ]]; then
    if ! .venv/bin/python -c 'import sys' >/dev/null 2>&1; then
      echo "Removing stale virtual environment (project moved or Python missing)..."
      rm -rf .venv
    elif ! .venv/bin/python -m pip --version >/dev/null 2>&1; then
      echo "Removing broken virtual environment (recreate after move or upgrade)..."
      rm -rf .venv
    fi
  fi
  if [[ ! -d .venv ]]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
  fi
}

ensure_venv

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing Python dependencies..."
python -m pip install -q -e .

python scripts/bootstrap.py ${BOOTSTRAP_ARGS[@]+"${BOOTSTRAP_ARGS[@]}"}

if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found. Install Node.js 18+ for the React UI."
  exit 1
fi

if [[ ! -d frontend/node_modules ]]; then
  echo "Installing frontend dependencies..."
  (cd frontend && npm install)
fi

cleanup() {
  if [[ -n "${API_PID:-}" ]]; then kill "$API_PID" 2>/dev/null || true; fi
  if [[ -n "${VITE_PID:-}" ]]; then kill "$VITE_PID" 2>/dev/null || true; fi
}
trap cleanup EXIT INT TERM

echo "Starting API on http://127.0.0.1:8000"
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload &
API_PID=$!

echo "Starting React UI on http://127.0.0.1:5173"
(cd frontend && npm run dev) &
VITE_PID=$!

wait "$VITE_PID"
