#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.runtime/prod/pids"

if [[ ! -d "$PID_DIR" ]]; then
  echo "[prod] Nenhum pid de producao encontrado."
else
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
fi

kill_port_listeners() {
  local port="$1"
  local pids=()
  local pid

  if command -v ss >/dev/null 2>&1; then
    mapfile -t pids < <(ss -ltnp "sport = :$port" 2>/dev/null \
      | awk -F'pid=' 'NR > 1 && NF > 1 {split($2, data, ","); print data[1]}' \
      | awk 'NF' \
      | sort -u)
  elif command -v lsof >/dev/null 2>&1; then
    mapfile -t pids < <(lsof -tiTCP:"$port" -sTCP:LISTEN 2>/dev/null | awk 'NF' | sort -u)
  elif command -v fuser >/dev/null 2>&1; then
    mapfile -t pids < <(fuser -n tcp "$port" 2>/dev/null | tr ' ' '\n' | awk 'NF' | sort -u)
  fi

  if (( ${#pids[@]} == 0 )); then
    return
  fi

  echo "[prod] Encerrando listeners remanescentes na porta $port: ${pids[*]}"
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  sleep 1
  for pid in "${pids[@]}"; do
    kill -9 "$pid" 2>/dev/null || true
  done
}

kill_port_listeners 3002
kill_port_listeners 3001
kill_port_listeners 3000
kill_port_listeners 8000

echo "[prod] Stack VM de producao parada."
