#!/usr/bin/env bash
set -euo pipefail

# Spectra-AIO setup script (Linux/macOS)
# Creates a virtual environment and installs backend dependencies.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then PYTHON_BIN="python3";
  elif command -v python >/dev/null 2>&1; then PYTHON_BIN="python";
  else
    echo "[ERROR] Python 3 not found. Install Python 3.10+ and retry." >&2
    exit 1
  fi
fi

echo "[*] Using Python: $PYTHON_BIN"
"$PYTHON_BIN" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3,10) else 1)' || {
  echo "[ERROR] Python 3.10+ is required." >&2
  exit 1
}

VENV_DIR="${VENV_DIR:-.venv}"
if [[ ! -d "$VENV_DIR" ]]; then
  echo "[*] Creating virtual environment: $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi

# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

python -m pip install --upgrade pip
python -m pip install -r backend/requirements.txt

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
  echo "[*] Created .env from .env.example"
fi

echo "[OK] Setup complete."
echo "Next steps:"
echo "  1) Activate venv: source $VENV_DIR/bin/activate"
echo "  2) Start Tor (default SOCKS: 127.0.0.1:9050), or adjust SPECTRA_TOR_PROXY in .env"
echo "  3) Run backend: ./run_backend.sh"
