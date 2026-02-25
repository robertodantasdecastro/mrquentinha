#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ADMIN_DIR="$ROOT_DIR/workspaces/web/admin"

if [[ ! -d "$ADMIN_DIR" ]]; then
  echo "[admin] Diretorio nao encontrado: $ADMIN_DIR" >&2
  exit 1
fi

ensure_npm() {
  if command -v npm >/dev/null 2>&1; then
    return 0
  fi

  local nvm_dir="${NVM_DIR:-$HOME/.nvm}"
  if [[ -s "$nvm_dir/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    source "$nvm_dir/nvm.sh"
    nvm use --silent default >/dev/null 2>&1 || nvm use --silent --lts >/dev/null 2>&1 || true
  fi

  command -v npm >/dev/null 2>&1
}

if ! ensure_npm; then
  echo "[admin] npm nao encontrado no PATH." >&2
  exit 1
fi

cd "$ADMIN_DIR"

if [[ ! -d node_modules ]]; then
  echo "[admin] Instalando dependencias..."
  npm install
fi

if [[ -z "${NEXT_PUBLIC_API_BASE_URL:-}" ]]; then
  primary_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "$primary_ip" ]]; then
    export NEXT_PUBLIC_API_BASE_URL="http://$primary_ip:8000"
  fi
fi

echo "[admin] NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL:-<auto-runtime>}"
echo "[admin] Iniciando Admin Web em http://0.0.0.0:3002"

child_pid=""

shutdown() {
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  echo "[admin] Encerrado."
  exit 0
}

trap shutdown INT TERM

npm run dev -- --hostname 0.0.0.0 --port 3002 &
child_pid=$!

set +e
wait "$child_pid"
status=$?
set -e

if [[ $status -eq 130 || $status -eq 143 ]]; then
  echo "[admin] Encerrado pelo usuario."
  exit 0
fi

exit "$status"
