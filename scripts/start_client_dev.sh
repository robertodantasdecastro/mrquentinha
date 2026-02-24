#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLIENT_DIR="$ROOT_DIR/workspaces/web/client"
CLIENT_PORT="${CLIENT_PORT:-3001}"
CLIENT_HOST="${CLIENT_HOST:-0.0.0.0}"
LOCK_FILE="$CLIENT_DIR/.next/dev/lock"

if [[ ! -d "$CLIENT_DIR" ]]; then
  echo "[client] Diretorio nao encontrado: $CLIENT_DIR" >&2
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
  echo "[client] npm nao encontrado no PATH." >&2
  exit 1
fi

list_port_pids() {
  local port="$1"

  if command -v ss >/dev/null 2>&1; then
    ss -ltnp "sport = :$port" 2>/dev/null \
      | awk -F'pid=' 'NR > 1 && NF > 1 {split($2, data, ","); print data[1]}' \
      | awk 'NF' \
      | sort -u
    return
  fi

  if command -v lsof >/dev/null 2>&1; then
    lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NF' | sort -u
    return
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -n tcp "$port" 2>/dev/null | tr ' ' '\n' | awk 'NF' | sort -u
    return
  fi
}

signal_pids() {
  local signal="$1"
  shift
  local pids=("$@")

  for pid in "${pids[@]}"; do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill "-$signal" "$pid" 2>/dev/null || true
    fi
  done
}

stop_pids_gracefully() {
  local pids=("$@")

  if (( ${#pids[@]} == 0 )); then
    return
  fi

  signal_pids INT "${pids[@]}"
  sleep 2
  signal_pids TERM "${pids[@]}"
  sleep 2
  signal_pids KILL "${pids[@]}"
}

cleanup_old_processes() {
  local pids=()

  mapfile -t pids < <(list_port_pids "$CLIENT_PORT" || true)
  if (( ${#pids[@]} > 0 )); then
    echo "[client] Encerrando processo(s) na porta $CLIENT_PORT: ${pids[*]}"
    stop_pids_gracefully "${pids[@]}"
  fi

  mapfile -t pids < <(pgrep -f "$CLIENT_DIR/node_modules/.bin/next dev" || true)
  if (( ${#pids[@]} > 0 )); then
    echo "[client] Encerrando next dev legado: ${pids[*]}"
    stop_pids_gracefully "${pids[@]}"
  fi
}

cleanup_old_processes

if [[ -f "$LOCK_FILE" ]]; then
  mapfile -t active_next < <(pgrep -f "$CLIENT_DIR/node_modules/.bin/next dev" || true)
  if (( ${#active_next[@]} == 0 )); then
    rm -f "$LOCK_FILE"
    echo "[client] Lock removido: $LOCK_FILE"
  else
    echo "[client] Lock mantido: existe next dev ativo (${active_next[*]})."
  fi
fi

cd "$CLIENT_DIR"

if [[ ! -d node_modules ]]; then
  echo "[client] Instalando dependencias..."
  npm install
fi

export NEXT_PUBLIC_API_BASE_URL="${NEXT_PUBLIC_API_BASE_URL:-http://127.0.0.1:8000}"
export NEXT_PUBLIC_DEMO_CUSTOMER_ID="${NEXT_PUBLIC_DEMO_CUSTOMER_ID:-1}"

echo "[client] NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL"
echo "[client] NEXT_PUBLIC_DEMO_CUSTOMER_ID=$NEXT_PUBLIC_DEMO_CUSTOMER_ID"
echo "[client] Iniciando Next.js em http://$CLIENT_HOST:$CLIENT_PORT"

child_pid=""

shutdown() {
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    stop_pids_gracefully "$child_pid"
    wait "$child_pid" 2>/dev/null || true
  fi

  echo "[client] Encerrado."
  exit 0
}

trap shutdown INT TERM

npm run dev -- --hostname "$CLIENT_HOST" --port "$CLIENT_PORT" &
child_pid=$!

set +e
wait "$child_pid"
status=$?
set -e

if [[ $status -eq 130 || $status -eq 143 ]]; then
  echo "[client] Encerrado pelo usuario."
  exit 0
fi

exit "$status"
