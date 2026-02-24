#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_SCRIPT="$ROOT_DIR/scripts/start_client_dev.sh"
CLIENT_DIR="$ROOT_DIR/workspaces/web/client"
CLIENT_PORT="${CLIENT_PORT:-3001}"
CLIENT_BASE_URL="http://127.0.0.1:${CLIENT_PORT}"
SMOKE_LOG="/tmp/mrq_smoke_client.log"
CLIENT_PID=""

if [[ ! -x "$START_SCRIPT" ]]; then
  echo "[smoke-client] Script nao encontrado ou sem permissao de execucao: $START_SCRIPT" >&2
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

http_status() {
  local url="$1"

  if command -v curl >/dev/null 2>&1; then
    curl -sS -o /dev/null -w "%{http_code}" "$url" || true
    return
  fi

  node -e '
    const http = require("http");
    const https = require("https");
    const target = process.argv[1];
    const client = target.startsWith("https://") ? https : http;
    const req = client.get(target, (res) => {
      process.stdout.write(String(res.statusCode));
      res.resume();
    });
    req.on("error", () => process.stdout.write("000"));
    req.setTimeout(5000, () => {
      req.destroy();
      process.stdout.write("000");
    });
  ' "$url" || true
}

wait_for_200() {
  local url="$1"
  local attempts="${2:-30}"

  for ((i = 1; i <= attempts; i++)); do
    local status_code
    status_code="$(http_status "$url")"
    if [[ "$status_code" == "200" ]]; then
      return 0
    fi
    sleep 1
  done

  echo "[smoke-client] Timeout aguardando 200 em: $url" >&2
  return 1
}

cleanup() {
  local status=$?
  local pids=()

  if [[ -n "$CLIENT_PID" ]] && kill -0 "$CLIENT_PID" 2>/dev/null; then
    stop_pids_gracefully "$CLIENT_PID"
    wait "$CLIENT_PID" 2>/dev/null || true
  fi

  mapfile -t pids < <(pgrep -f "$CLIENT_DIR/node_modules/.bin/next dev" || true)
  stop_pids_gracefully "${pids[@]}"

  mapfile -t pids < <(list_port_pids "$CLIENT_PORT" || true)
  stop_pids_gracefully "${pids[@]}"

  if [[ $status -ne 0 ]]; then
    echo "[smoke-client] Falhou. Ultimas linhas do log:" >&2
    tail -n 60 "$SMOKE_LOG" >&2 || true
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM

echo "[smoke-client] Subindo client em background..."
CLIENT_PORT="$CLIENT_PORT" "$START_SCRIPT" >"$SMOKE_LOG" 2>&1 &
CLIENT_PID=$!

echo "[smoke-client] Aguardando client responder..."
wait_for_200 "$CLIENT_BASE_URL/"

for route in "/" "/pedidos" "/cardapio"; do
  status_code="$(http_status "${CLIENT_BASE_URL}${route}")"
  if [[ "$status_code" != "200" ]]; then
    echo "[smoke-client] Rota ${route} retornou status ${status_code}" >&2
    exit 1
  fi
  echo "[smoke-client] OK ${route} -> ${status_code}"
done

echo "[smoke-client] OK: client validado."
