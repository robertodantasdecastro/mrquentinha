#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORTAL_DIR="$ROOT_DIR/workspaces/web/portal"

if [[ ! -d "$PORTAL_DIR" ]]; then
  echo "[portal] Diretorio nao encontrado: $PORTAL_DIR" >&2
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[portal] npm nao encontrado no PATH." >&2
  exit 1
fi

cd "$PORTAL_DIR"

if [[ ! -d node_modules ]]; then
  echo "[portal] Instalando dependencias..."
  npm install
fi

echo "[portal] Iniciando Next.js em http://0.0.0.0:3000"

child_pid=""

shutdown() {
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  echo "[portal] Encerrado."
  exit 0
}

trap shutdown INT TERM

npm run dev -- --hostname 0.0.0.0 --port 3000 &
child_pid=$!

set +e
wait "$child_pid"
status=$?
set -e

if [[ $status -eq 130 || $status -eq 143 ]]; then
  echo "[portal] Encerrado pelo usuario."
  exit 0
fi

exit "$status"
