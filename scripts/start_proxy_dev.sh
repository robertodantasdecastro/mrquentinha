#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONF_FILE="$ROOT_DIR/infra/nginx/dev_proxy.conf"
RUNTIME_DIR="$ROOT_DIR/.runtime/nginx"
PID_FILE="$RUNTIME_DIR/nginx.pid"

if ! command -v nginx >/dev/null 2>&1; then
  echo "[proxy] nginx nao encontrado." >&2
  echo "[proxy] Instale com: sudo apt-get update && sudo apt-get install -y nginx" >&2
  exit 1
fi

if [[ ! -f "$CONF_FILE" ]]; then
  echo "[proxy] Configuracao nao encontrada: $CONF_FILE" >&2
  exit 1
fi

mkdir -p "$RUNTIME_DIR"

if [[ -f "$PID_FILE" ]]; then
  running_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "$running_pid" ]] && kill -0 "$running_pid" 2>/dev/null; then
    echo "[proxy] nginx ja esta ativo (pid=$running_pid)."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

nginx -t -p "$ROOT_DIR" -c "$CONF_FILE"
nginx -p "$ROOT_DIR" -c "$CONF_FILE"

sleep 1
if [[ -f "$PID_FILE" ]]; then
  echo "[proxy] nginx iniciado (pid=$(cat "$PID_FILE"))."
else
  echo "[proxy] nginx iniciou, mas pid file nao foi encontrado." >&2
fi

echo "[proxy] Rotas locais via http://127.0.0.1:8088"
echo "[proxy] - Host: api.mrquentinha.local   -> backend:8000"
echo "[proxy] - Host: www.mrquentinha.local   -> portal:3000"
echo "[proxy] - Host: app.mrquentinha.local   -> client:3001"
echo "[proxy] - Host: admin.mrquentinha.local -> admin:3002"
