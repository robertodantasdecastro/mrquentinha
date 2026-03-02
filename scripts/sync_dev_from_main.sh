#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"

DB_USER="${MRQ_DB_USER:-mrq_user}"
DB_PASS="${MRQ_DB_PASS:-hDgXuv1y*2170tor}"
DB_HOST="${MRQ_DB_HOST:-127.0.0.1}"
DB_PORT="${MRQ_DB_PORT:-5432}"
DB_NAME="${MRQ_DB_DEV_NAME:-mrquentinha_dev}"

AUTO_STASH="${MRQ_DEV_AUTO_STASH:-1}"
INSTALL_FRONTEND_DEPS="${MRQ_DEV_INSTALL_FRONTEND_DEPS:-1}"

log() {
  echo "[sync-dev] $*"
}

die() {
  echo "[sync-dev] ERRO: $*" >&2
  exit 1
}

ensure_repo() {
  [[ -d "$ROOT_DIR/.git" ]] || die "Repositorio git nao encontrado em $ROOT_DIR"
}

sync_main() {
  cd "$ROOT_DIR"
  log "Atualizando refs remotas..."
  git fetch origin --prune

  if [[ -n "$(git status --porcelain)" ]]; then
    if [[ "$AUTO_STASH" == "1" ]]; then
      log "Worktree sujo. Salvando stash automatico..."
      git stash push -u -m "sync-dev:auto-stash:$(date +%Y%m%d-%H%M%S)"
    else
      die "Worktree com alteracoes locais. Defina MRQ_DEV_AUTO_STASH=1 ou limpe antes."
    fi
  fi

  log "Sincronizando branch main..."
  git checkout main
  git pull --ff-only origin main
}

ensure_env_file() {
  cd "$BACKEND_DIR"
  [[ -f .env.dev ]] || cp .env.example .env.dev

  sed -i '/^DATABASE_URL=/d' .env.dev
  printf 'DATABASE_URL=postgresql://%s:%s@%s:%s/%s\n' \
    "$DB_USER" "$DB_PASS" "$DB_HOST" "$DB_PORT" "$DB_NAME" >> .env.dev

  grep -q '^DJANGO_SETTINGS_MODULE=' .env.dev || echo 'DJANGO_SETTINGS_MODULE=config.settings.dev' >> .env.dev
  grep -q '^DEBUG=' .env.dev || echo 'DEBUG=True' >> .env.dev
  grep -q '^SECRET_KEY=' .env.dev || echo "SECRET_KEY=dev-$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" >> .env.dev

  ln -sfn .env.dev .env
}

ensure_postgres() {
  log "Garantindo role/banco local no Postgres..."
  sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASS}' CREATEDB;"

  sudo -u postgres psql -c "ALTER ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASS}' CREATEDB;"

  sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"
}

backend_migrate() {
  cd "$BACKEND_DIR"
  source .venv/bin/activate
  log "Aplicando migracoes e checks do backend..."
  python manage.py migrate --noinput
  python manage.py check
}

install_frontend_deps() {
  if [[ "$INSTALL_FRONTEND_DEPS" != "1" ]]; then
    log "Instalacao de deps frontend ignorada (MRQ_DEV_INSTALL_FRONTEND_DEPS=0)."
    return 0
  fi

  log "Instalando dependencias frontend..."
  cd "$ROOT_DIR/workspaces/web/ui" && npm ci --no-audit --fund=false || npm install
  cd "$ROOT_DIR/workspaces/web/admin" && npm ci --no-audit --fund=false || npm install
  cd "$ROOT_DIR/workspaces/web/portal" && npm ci --no-audit --fund=false || npm install
  cd "$ROOT_DIR/workspaces/web/client" && npm ci --no-audit --fund=false || npm install
}

restart_dev_stack() {
  cd "$ROOT_DIR"
  mkdir -p .runtime

  log "Reiniciando servicos DEV..."
  pkill -f "manage.py runserver 0.0.0.0:8000" || true
  pkill -f "next dev --webpack" || true

  nohup bash scripts/start_backend_dev.sh > .runtime/dev-backend.log 2>&1 &
  nohup bash scripts/start_portal_dev.sh > .runtime/dev-portal.log 2>&1 &
  nohup bash scripts/start_client_dev.sh > .runtime/dev-client.log 2>&1 &
  nohup bash scripts/start_admin_dev.sh > .runtime/dev-admin.log 2>&1 &
}

smoke() {
  log "Executando smoke rapido..."
  sleep 10
  curl -fsS "http://127.0.0.1:8000/api/v1/health" >/dev/null
  curl -fsS -o /dev/null "http://127.0.0.1:3000"
  curl -fsS -o /dev/null "http://127.0.0.1:3001"
  curl -fsS -o /dev/null "http://127.0.0.1:3002"
  log "Smoke OK: backend(8000) portal(3000) client(3001) admin(3002)"
}

main() {
  ensure_repo
  sync_main
  ensure_env_file
  ensure_postgres
  backend_migrate
  install_frontend_deps
  restart_dev_stack
  smoke
  log "Sincronizacao DEV finalizada com sucesso."
}

main "$@"
