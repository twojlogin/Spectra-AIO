#!/usr/bin/env bash
set -euo pipefail
# Convenience launcher: setup (if needed) + run backend
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

if [[ ! -d .venv ]]; then
  ./setup.sh
fi

./run_backend.sh
