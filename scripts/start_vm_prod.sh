#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.runtime/prod"
PID_DIR="$RUNTIME_DIR/pids"
LOG_DIR="$RUNTIME_DIR/logs"

BACKEND_DIR="$ROOT_DIR/workspaces/backend"
PORTAL_DIR="$ROOT_DIR/workspaces/web/portal"
CLIENT_DIR="$ROOT_DIR/workspaces/web/client"
ADMIN_DIR="$ROOT_DIR/workspaces/web/admin"
INTERNAL_API_BASE_URL="${MRQ_INTERNAL_API_BASE_URL:-http://127.0.0.1:8000}"
GUNICORN_WORKERS="${MRQ_GUNICORN_WORKERS:-1}"
GUNICORN_TIMEOUT="${MRQ_GUNICORN_TIMEOUT:-120}"
NODE_MAX_OLD_SPACE_MB="${MRQ_NODE_MAX_OLD_SPACE_MB:-256}"
STARTUP_WAIT_SECONDS="${MRQ_STARTUP_WAIT_SECONDS:-3}"

mkdir -p "$PID_DIR" "$LOG_DIR"

start_service() {
  local key="$1"
  local command="$2"
  local pid_file="$PID_DIR/${key}.pid"
  local log_file="$LOG_DIR/${key}.log"

  if [[ -f "$pid_file" ]]; then
    local existing_pid
    existing_pid="$(cat "$pid_file")"
    if [[ -n "$existing_pid" ]] && kill -0 "$existing_pid" 2>/dev/null; then
      echo "[prod] $key ja esta em execucao (pid=$existing_pid)."
      return
    fi
    rm -f "$pid_file"
  fi

  nohup bash -lc "$command" >"$log_file" 2>&1 &
  local pid=$!
  echo "$pid" > "$pid_file"
  sleep "$STARTUP_WAIT_SECONDS"
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "[prod] Falha ao iniciar $key. Ultimas linhas do log:" >&2
    tail -n 80 "$log_file" >&2 || true
    rm -f "$pid_file"
    exit 1
  fi

  echo "[prod] $key iniciado (pid=$pid). log=$log_file"
}

if [[ ! -f "$BACKEND_DIR/.venv/bin/activate" ]]; then
  echo "[prod] Venv do backend nao encontrada em $BACKEND_DIR/.venv" >&2
  exit 1
fi

if [[ ! -f "$BACKEND_DIR/.env.prod" ]]; then
  echo "[prod] Arquivo .env.prod nao encontrado em $BACKEND_DIR" >&2
  exit 1
fi

if [[ ! -d "$PORTAL_DIR/node_modules" || ! -d "$CLIENT_DIR/node_modules" || ! -d "$ADMIN_DIR/node_modules" ]]; then
  echo "[prod] Dependencias Node ausentes. Rode o instalador primeiro." >&2
  exit 1
fi

if [[ ! -d "$PORTAL_DIR/.next" || ! -d "$CLIENT_DIR/.next" || ! -d "$ADMIN_DIR/.next" ]]; then
  echo "[prod] Build dos frontends ausente. Executando build..."
  (cd "$PORTAL_DIR" && npm run build)
  (cd "$CLIENT_DIR" && npm run build)
  (cd "$ADMIN_DIR" && npm run build)
fi

ln -sfn .env.prod "$BACKEND_DIR/.env"

start_service "backend" "source '$BACKEND_DIR/.venv/bin/activate' && cd '$BACKEND_DIR' && DJANGO_SETTINGS_MODULE=config.settings.prod DEBUG=False python manage.py migrate --noinput && gunicorn config.wsgi:application --chdir '$BACKEND_DIR/src' --bind 127.0.0.1:8000 --workers '$GUNICORN_WORKERS' --timeout '$GUNICORN_TIMEOUT'"
start_service "portal" "cd '$PORTAL_DIR' && NODE_OPTIONS='--max-old-space-size=${NODE_MAX_OLD_SPACE_MB}' INTERNAL_API_BASE_URL='${INTERNAL_API_BASE_URL}' NEXT_PUBLIC_API_BASE_URL='${INTERNAL_API_BASE_URL}' npm run start -- --hostname 127.0.0.1 --port 3000"
start_service "client" "cd '$CLIENT_DIR' && NODE_OPTIONS='--max-old-space-size=${NODE_MAX_OLD_SPACE_MB}' INTERNAL_API_BASE_URL='${INTERNAL_API_BASE_URL}' NEXT_PUBLIC_API_BASE_URL='${INTERNAL_API_BASE_URL}' npm run start -- --hostname 127.0.0.1 --port 3001"
start_service "admin" "cd '$ADMIN_DIR' && NODE_OPTIONS='--max-old-space-size=${NODE_MAX_OLD_SPACE_MB}' INTERNAL_API_BASE_URL='${INTERNAL_API_BASE_URL}' NEXT_PUBLIC_API_BASE_URL='${INTERNAL_API_BASE_URL}' npm run start -- --hostname 127.0.0.1 --port 3002"

echo "[prod] Stack VM de producao inicializada."
echo "[prod] Use scripts/stop_vm_prod.sh para parar e scripts/start_proxy_dev.sh para proxy local opcional."
