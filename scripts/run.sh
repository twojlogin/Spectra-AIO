#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
if [ -f ".venv/bin/activate" ]; then source ".venv/bin/activate"; fi
HOST="${SPECTRA_HOST:-127.0.0.1}"
PORT="${SPECTRA_PORT:-8000}"
exec python -m uvicorn backend.main_backend:app --host "$HOST" --port "$PORT"
