#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
START_SCRIPT="$ROOT_DIR/scripts/start_client_dev.sh"
CLIENT_DIR="$ROOT_DIR/workspaces/web/client"
CLIENT_PORT="${CLIENT_PORT:-3001}"
CLIENT_BASE_URL="http://127.0.0.1:${CLIENT_PORT}"
START_TIMEOUT_SECONDS="${START_TIMEOUT_SECONDS:-30}"
SMOKE_LOG="/tmp/mrq_smoke_client.log"
CLIENT_PID=""
LOG_ALREADY_PRINTED=0

if [[ ! -x "$START_SCRIPT" ]]; then
  echo "[smoke-client] Script nao encontrado ou sem permissao de execucao: $START_SCRIPT" >&2
  exit 1
fi

if ! [[ "$START_TIMEOUT_SECONDS" =~ ^[0-9]+$ ]] || (( START_TIMEOUT_SECONDS <= 0 )); then
  echo "[smoke-client] START_TIMEOUT_SECONDS invalido: $START_TIMEOUT_SECONDS" >&2
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

print_client_log() {
  if (( LOG_ALREADY_PRINTED == 1 )); then
    return
  fi

  LOG_ALREADY_PRINTED=1
  echo "[smoke-client] Ultimas linhas do log do client:" >&2
  tail -n 60 "$SMOKE_LOG" >&2 || true
}

http_status() {
  local url="$1"

  if command -v curl >/dev/null 2>&1; then
    curl -sS -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || true
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

wait_for_client() {
  local deadline=$((SECONDS + START_TIMEOUT_SECONDS))

  while (( SECONDS < deadline )); do
    local status_code
    status_code="$(http_status "$CLIENT_BASE_URL/")"

    if [[ "$status_code" == "200" ]]; then
      return 0
    fi

    if [[ -n "$CLIENT_PID" ]] && ! kill -0 "$CLIENT_PID" 2>/dev/null; then
      echo "[smoke-client] Client encerrou antes de ficar disponivel." >&2
      print_client_log
      return 1
    fi

    sleep 1
  done

  echo "[smoke-client] Timeout (${START_TIMEOUT_SECONDS}s) aguardando 200 em ${CLIENT_BASE_URL}/" >&2
  print_client_log
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
    print_client_log
  fi

  exit "$status"
}

trap cleanup EXIT INT TERM

: > "$SMOKE_LOG"

echo "[smoke-client] Subindo client em background..."
CLIENT_PORT="$CLIENT_PORT" "$START_SCRIPT" >"$SMOKE_LOG" 2>&1 &
CLIENT_PID=$!

echo "[smoke-client] Aguardando client responder..."
wait_for_client

for route in "/" "/pedidos" "/cardapio"; do
  status_code="$(http_status "${CLIENT_BASE_URL}${route}")"
  if [[ "$status_code" != "200" ]]; then
    echo "[smoke-client] Rota ${route} retornou status ${status_code}" >&2
    print_client_log
    exit 1
  fi
  echo "[smoke-client] OK ${route} -> ${status_code}"
done

echo "[smoke-client] OK: client validado."
