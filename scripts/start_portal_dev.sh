#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORTAL_DIR="$ROOT_DIR/workspaces/web/portal"
API_RESOLVER_SCRIPT="$ROOT_DIR/scripts/resolve_api_base_from_backend.sh"

if [[ ! -d "$PORTAL_DIR" ]]; then
  echo "[portal] Diretorio nao encontrado: $PORTAL_DIR" >&2
  exit 1
fi

if [[ ! -x "$API_RESOLVER_SCRIPT" ]]; then
  chmod +x "$API_RESOLVER_SCRIPT" 2>/dev/null || true
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

read_env_local_value() {
  local file_path="$1"
  local key_name="$2"

  if [[ ! -f "$file_path" ]]; then
    return 1
  fi

  local raw_value
  raw_value="$(awk -F= -v key="$key_name" '$1 == key {print substr($0, index($0, "=") + 1); exit}' "$file_path")"
  if [[ -z "$raw_value" ]]; then
    return 1
  fi

  raw_value="${raw_value%\"}"
  raw_value="${raw_value#\"}"
  printf '%s' "$raw_value"
}

if ! ensure_npm; then
  echo "[portal] npm nao encontrado no PATH." >&2
  exit 1
fi

cd "$PORTAL_DIR"

if [[ ! -d node_modules ]]; then
  echo "[portal] Instalando dependencias..."
  npm install
fi

if [[ -z "${NEXT_PUBLIC_API_BASE_URL:-}" ]]; then
  env_local_value="$(read_env_local_value "$PORTAL_DIR/.env.local" "NEXT_PUBLIC_API_BASE_URL" || true)"
  if [[ -n "${env_local_value:-}" ]]; then
    export NEXT_PUBLIC_API_BASE_URL="$env_local_value"
    echo "[portal] NEXT_PUBLIC_API_BASE_URL carregado de .env.local"
  fi
fi

export INTERNAL_API_BASE_URL="${INTERNAL_API_BASE_URL:-http://127.0.0.1:8000}"
export PORTAL_API_BASE_URL="${PORTAL_API_BASE_URL:-$INTERNAL_API_BASE_URL}"

if [[ -z "${NEXT_PUBLIC_API_BASE_URL:-}" ]]; then
  resolved_api_base_url="$("$API_RESOLVER_SCRIPT" portal home 2>/dev/null || true)"
  if [[ -n "${resolved_api_base_url:-}" ]]; then
    export NEXT_PUBLIC_API_BASE_URL="$resolved_api_base_url"
    echo "[portal] NEXT_PUBLIC_API_BASE_URL resolvido via backend config"
  fi
fi

if [[ -z "${NEXT_PUBLIC_API_BASE_URL:-}" ]]; then
  primary_ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  if [[ -n "$primary_ip" ]]; then
    export NEXT_PUBLIC_API_BASE_URL="http://$primary_ip:8000"
  else
    export NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
  fi
fi

echo "[portal] NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL"
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
