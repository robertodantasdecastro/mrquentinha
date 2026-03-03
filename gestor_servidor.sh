#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

PY_BIN="python3"
if [[ -x "$ROOT_DIR/workspaces/backend/.venv/bin/python" ]]; then
  PY_BIN="$ROOT_DIR/workspaces/backend/.venv/bin/python"
fi

export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

exec "$PY_BIN" -m GestorServidor.app "$@"
