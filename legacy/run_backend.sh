#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

VENV_DIR="${VENV_DIR:-.venv}"
if [[ -f "$VENV_DIR/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
fi

HOST="${SPECTRA_HOST:-127.0.0.1}"
PORT="${SPECTRA_PORT:-8000}"

echo "[*] Starting Spectra-AIO backend on http://${HOST}:${PORT}"
exec python -m uvicorn backend.main_backend:app --host "$HOST" --port "$PORT"
