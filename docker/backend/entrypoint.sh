#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-${APP_MODE:-dev}}"
BACKEND_DIR="/app/workspaces/backend"

wait_for_postgres() {
  local max_wait="${DB_WAIT_SECONDS:-45}"
  local elapsed=0

  echo "[backend-container] Aguardando PostgreSQL..."
  while ! python - <<'PY' >/dev/null 2>&1
import os
import psycopg

url = os.environ.get("DATABASE_URL", "")
if not url:
    raise SystemExit(1)

with psycopg.connect(url, connect_timeout=3) as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
PY
  do
    sleep 2
    elapsed=$((elapsed + 2))
    if [ "$elapsed" -ge "$max_wait" ]; then
      echo "[backend-container] ERRO: timeout ao aguardar PostgreSQL." >&2
      exit 1
    fi
  done
  echo "[backend-container] PostgreSQL pronto."
}

cd "$BACKEND_DIR"
wait_for_postgres

if [ "${AUTO_MIGRATE:-1}" = "1" ]; then
  echo "[backend-container] Aplicando migracoes..."
  python manage.py migrate --noinput
fi

if [ "$MODE" = "prod" ]; then
  export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.prod}"
  echo "[backend-container] Iniciando Gunicorn (modo producao)..."
  exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${GUNICORN_WORKERS:-3}" \
    --timeout "${GUNICORN_TIMEOUT:-120}" \
    --chdir /app/workspaces/backend/src
fi

export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.dev}"
echo "[backend-container] Iniciando Django runserver (modo desenvolvimento)..."
exec python manage.py runserver 0.0.0.0:8000
