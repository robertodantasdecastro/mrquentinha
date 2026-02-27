#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime/ops"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$RUNTIME_DIR/logs"
PID_FILE="$PID_DIR/cloudflare.pid"
LOG_FILE="$LOG_DIR/cloudflare.log"
LOCAL_BIN="$ROOT_DIR/.runtime/bin/cloudflared"

mkdir -p "$PID_DIR" "$LOG_DIR"

read_pid() {
  if [[ ! -f "$PID_FILE" ]]; then
    return 1
  fi

  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -z "$pid" ]]; then
    return 1
  fi

  if kill -0 "$pid" 2>/dev/null; then
    printf '%s' "$pid"
    return 0
  fi

  rm -f "$PID_FILE"
  return 1
}

resolve_command() {
  local cloudflared_bin="${MQ_CLOUDFLARED_BIN:-}"
  if [[ -z "$cloudflared_bin" ]]; then
    if [[ -x "$LOCAL_BIN" ]]; then
      cloudflared_bin="$LOCAL_BIN"
    else
      cloudflared_bin="$(command -v cloudflared || true)"
    fi
  fi

  if [[ -z "$cloudflared_bin" ]]; then
    echo "[cloudflare] binario 'cloudflared' nao encontrado no PATH nem em $LOCAL_BIN." >&2
    exit 1
  fi

  local token="${CF_TUNNEL_TOKEN:-}"
  local name="${CF_TUNNEL_NAME:-mrquentinha}"

  if [[ -n "$token" ]]; then
    printf '%s\ntunnel\nrun\n--token\n%s\n' "$cloudflared_bin" "$token"
    return 0
  fi

  if [[ -n "$name" ]]; then
    printf '%s\ntunnel\nrun\n%s\n' "$cloudflared_bin" "$name"
    return 0
  fi

  echo "[cloudflare] Defina CF_TUNNEL_TOKEN ou CF_TUNNEL_NAME." >&2
  exit 1
}

start_tunnel() {
  if existing_pid="$(read_pid)"; then
    echo "[cloudflare] tunnel ja esta em execucao (pid=$existing_pid)."
    exit 0
  fi

  mapfile -t cmd_parts < <(resolve_command)
  nohup "${cmd_parts[@]}" >>"$LOG_FILE" 2>&1 < /dev/null &
  local pid=$!
  echo "$pid" > "$PID_FILE"

  sleep 0.2
  if kill -0 "$pid" 2>/dev/null; then
    echo "[cloudflare] tunnel iniciado (pid=$pid)."
    echo "[cloudflare] log: $LOG_FILE"
    exit 0
  fi

  rm -f "$PID_FILE"
  echo "[cloudflare] falha ao iniciar tunnel. Verifique o log: $LOG_FILE" >&2
  exit 1
}

stop_tunnel() {
  local pid
  if ! pid="$(read_pid)"; then
    echo "[cloudflare] tunnel nao esta em execucao."
    exit 0
  fi

  kill "$pid" 2>/dev/null || true
  sleep 0.5
  if kill -0 "$pid" 2>/dev/null; then
    kill -9 "$pid" 2>/dev/null || true
  fi

  rm -f "$PID_FILE"
  echo "[cloudflare] tunnel parado."
}

status_tunnel() {
  if pid="$(read_pid)"; then
    echo "[cloudflare] status=running pid=$pid log=$LOG_FILE"
    exit 0
  fi

  echo "[cloudflare] status=stopped log=$LOG_FILE"
}

logs_tunnel() {
  if [[ ! -f "$LOG_FILE" ]]; then
    echo "[cloudflare] log ainda nao existe: $LOG_FILE"
    exit 0
  fi

  tail -n "${1:-80}" "$LOG_FILE"
}

command="${1:-status}"
case "$command" in
  start)
    start_tunnel
    ;;
  stop)
    stop_tunnel
    ;;
  restart)
    stop_tunnel
    start_tunnel
    ;;
  status)
    status_tunnel
    ;;
  logs)
    logs_tunnel "${2:-80}"
    ;;
  *)
    echo "Uso: $0 {start|stop|restart|status|logs [linhas]}" >&2
    exit 1
    ;;
esac
