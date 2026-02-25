#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF_FILE="$ROOT_DIR/infra/nginx/dev_proxy.conf"
PID_FILE="$ROOT_DIR/.runtime/nginx/nginx.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "[proxy] nginx dev nao esta ativo (sem pid file)."
  exit 0
fi

running_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "$running_pid" ]] || ! kill -0 "$running_pid" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "[proxy] pid file limpo (processo inexistente)."
  exit 0
fi

nginx -s quit -p "$ROOT_DIR" -c "$CONF_FILE" || kill "$running_pid" 2>/dev/null || true
sleep 1

if kill -0 "$running_pid" 2>/dev/null; then
  kill -TERM "$running_pid" 2>/dev/null || true
fi

rm -f "$PID_FILE"
echo "[proxy] nginx dev encerrado."
