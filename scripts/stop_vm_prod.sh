#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.runtime/prod/pids"

if [[ ! -d "$PID_DIR" ]]; then
  echo "[prod] Nenhum pid de producao encontrado."
  exit 0
fi

stop_service() {
  local key="$1"
  local pid_file="$PID_DIR/${key}.pid"

  if [[ ! -f "$pid_file" ]]; then
    echo "[prod] $key sem pid registrado."
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
    kill "$pid" 2>/dev/null || true
    sleep 1
    kill -9 "$pid" 2>/dev/null || true
    echo "[prod] $key parado (pid=$pid)."
  else
    echo "[prod] $key ja estava parado."
  fi

  rm -f "$pid_file"
}

stop_service "admin"
stop_service "client"
stop_service "portal"
stop_service "backend"

echo "[prod] Stack VM de producao parada."
