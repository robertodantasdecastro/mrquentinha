#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Uso:
  scripts/sync_dev_then_prod.sh --dev
  scripts/sync_dev_then_prod.sh --prod

Variaveis opcionais:
  MRQ_DEV_ROOT (default: $HOME/mrquentinha)
  MRQ_PROD_ROOT (default: /home/ubuntu/mrquentinha)
  MRQ_GIT_USER_NAME (default: robertodantasdecastro)
  MRQ_GIT_USER_EMAIL (default: robertodantasdecastro@gmail.com)
USAGE
}

log() {
  printf '\n[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

append_csv_item() {
  local file_path="$1"
  local key="$2"
  local item="$3"
  local line_number current_value

  line_number="$(rg -n "^${key}=" "$file_path" | head -n1 | cut -d: -f1 || true)"
  if [[ -z "$line_number" ]]; then
    printf '%s=%s\n' "$key" "$item" >> "$file_path"
    return 0
  fi

  current_value="$(sed -n "${line_number}p" "$file_path" | cut -d= -f2-)"
  if [[ ",${current_value}," == *",${item},"* ]]; then
    return 0
  fi

  sed -i "${line_number}s|$|,${item}|" "$file_path"
}

run_dev() {
  local root="${MRQ_DEV_ROOT:-$HOME/mrquentinha}"
  local git_user_name="${MRQ_GIT_USER_NAME:-robertodantasdecastro}"
  local git_user_email="${MRQ_GIT_USER_EMAIL:-robertodantasdecastro@gmail.com}"

  log "DEV: sincronizando repositorio em ${root}"
  cd "$root"
  git fetch origin
  git checkout main
  git pull --ff-only origin main

  log "DEV: configurando git global"
  git config --global user.name "$git_user_name"
  git config --global user.email "$git_user_email"

  log "DEV: backend"
  cd "$root/workspaces/backend"
  python3 -m venv .venv || true
  source .venv/bin/activate
  pip install -U pip setuptools wheel
  pip install -r requirements.txt -r requirements-dev.txt
  [[ -f .env.dev ]] || cp .env.example .env.dev
  append_csv_item .env.dev CORS_ALLOWED_ORIGINS http://localhost:3002
  append_csv_item .env.dev CORS_ALLOWED_ORIGINS http://127.0.0.1:3002
  append_csv_item .env.dev CORS_ALLOWED_ORIGINS http://10.211.55.21:3002
  append_csv_item .env.dev CSRF_TRUSTED_ORIGINS http://localhost:3002
  append_csv_item .env.dev CSRF_TRUSTED_ORIGINS http://127.0.0.1:3002
  append_csv_item .env.dev CSRF_TRUSTED_ORIGINS http://10.211.55.21:3002
  ln -sfn .env.dev .env
  export DJANGO_SETTINGS_MODULE=config.settings.dev
  python manage.py migrate --noinput
  python manage.py collectstatic --noinput
  python manage.py check

  log "DEV: dependencias frontend"
  cd "$root/workspaces/web/ui" && npm ci --no-audit --fund=false || npm install
  cd "$root/workspaces/web/admin" && npm ci --no-audit --fund=false || npm install
  cd "$root/workspaces/web/portal" && npm ci --no-audit --fund=false || npm install
  cd "$root/workspaces/web/client" && npm ci --no-audit --fund=false || npm install

  log "DEV: restart da stack"
  cd "$root"
  pkill -f 'manage.py runserver 0.0.0.0:8000' || true
  pkill -f 'next dev --webpack' || true
  nohup bash scripts/start_backend_dev.sh > .runtime/dev-backend.log 2>&1 &
  nohup bash scripts/start_portal_dev.sh  > .runtime/dev-portal.log 2>&1 &
  nohup bash scripts/start_client_dev.sh  > .runtime/dev-client.log 2>&1 &
  nohup bash scripts/start_admin_dev.sh   > .runtime/dev-admin.log 2>&1 &

  log "DEV: smoke"
  sleep 8
  curl -fsS http://127.0.0.1:8000/api/v1/health && echo
  echo "OK DEV sincronizada com main."
}

run_prod() {
  local root="${MRQ_PROD_ROOT:-/home/ubuntu/mrquentinha}"

  log "PROD: sincronizando repositorio em ${root}"
  cd "$root"
  git fetch origin
  git checkout main
  git pull --ff-only origin main

  log "PROD: backend (env prod explicito)"
  cd "$root/workspaces/backend"
  ln -sfn .env.prod .env
  export DJANGO_SETTINGS_MODULE=config.settings.prod
  source .venv/bin/activate
  python manage.py migrate --noinput
  python manage.py check

  log "PROD: build frontend"
  cd "$root/workspaces/web/portal" && npm ci --no-audit --fund=false || npm install
  npm run build
  cd "$root/workspaces/web/client" && npm ci --no-audit --fund=false || npm install
  npm run build
  cd "$root/workspaces/web/admin" && npm ci --no-audit --fund=false || npm install
  npm run build

  log "PROD: restart servicos"
  sudo systemctl restart mrq-backend-prod mrq-portal-prod mrq-client-prod mrq-admin-prod
  sudo systemctl is-active mrq-backend-prod mrq-portal-prod mrq-client-prod mrq-admin-prod

  log "PROD: smoke dominios"
  curl -fsS https://admin.mrquentinha.com.br/api/v1/health && echo
  curl -I -sS https://www.mrquentinha.com.br | head -n 5
  curl -I -sS https://app.mrquentinha.com.br | head -n 5
  curl -I -sS https://admin.mrquentinha.com.br | head -n 5
  curl -I -sS https://web.mrquentinha.com.br | head -n 5

  log "PROD: API e CORS"
  curl -fsS https://api.mrquentinha.com.br/api/v1/health && echo
  curl -sS -D - -o /tmp/cors.out -X OPTIONS https://api.mrquentinha.com.br/api/v1/health \
    -H 'Origin: https://app.mrquentinha.com.br' \
    -H 'Access-Control-Request-Method: GET'
  grep -i 'access-control-allow-origin' /tmp/cors.out

  echo "OK PROD sincronizada com main."
}

main() {
  if [[ $# -ne 1 ]]; then
    usage
    exit 1
  fi

  case "$1" in
    --dev)
      run_dev
      ;;
    --prod)
      run_prod
      ;;
    -h|--help)
      usage
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
