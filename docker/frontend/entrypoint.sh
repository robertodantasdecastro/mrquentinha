#!/usr/bin/env bash
set -euo pipefail

MODE="${1:-${APP_MODE:-dev}}"
APP_NAME="${APP_NAME:-portal}"
APP_PORT="${APP_PORT:-3000}"
APP_DIR="/app/workspaces/web/${APP_NAME}"

if [ ! -d "$APP_DIR" ]; then
  echo "[frontend-container] ERRO: app nao encontrado: $APP_DIR" >&2
  exit 1
fi

cd "$APP_DIR"

if [ ! -d node_modules ]; then
  echo "[frontend-container] node_modules ausente em ${APP_NAME}. Instalando..."
  npm install
fi

if [ "$MODE" = "prod" ]; then
  echo "[frontend-container] Build de producao para ${APP_NAME}..."
  npm run build
  echo "[frontend-container] Iniciando ${APP_NAME} em modo producao na porta ${APP_PORT}..."
  exec npm run start -- --hostname 0.0.0.0 --port "$APP_PORT"
fi

echo "[frontend-container] Iniciando ${APP_NAME} em modo desenvolvimento na porta ${APP_PORT}..."
exec npm run dev -- --hostname 0.0.0.0 --port "$APP_PORT"
