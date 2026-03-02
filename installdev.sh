#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"
ENV_DEV="$BACKEND_DIR/.env.dev"
ENV_PROD="$BACKEND_DIR/.env.prod"

DB_USER="${MRQ_DB_USER:-mrq_user}"
DB_PASS="${MRQ_DB_PASS:-}"
DB_DEV_NAME="${MRQ_DB_DEV_NAME:-mrquentinha_dev}"
DB_PROD_NAME="${MRQ_DB_PROD_NAME:-mrquentinha_prod}"
DEV_DUMP_PATH="${MRQ_DEV_DB_DUMP_PATH:-}"
DEV_DUMP_URL="${MRQ_DEV_DB_DUMP_URL:-}"

ROOT_DOMAIN="${MRQ_ROOT_DOMAIN:-mrquentinha.com.br}"
PORTAL_DOMAIN="${MRQ_PORTAL_DOMAIN:-www.${ROOT_DOMAIN}}"
CLIENT_DOMAIN="${MRQ_CLIENT_DOMAIN:-app.${ROOT_DOMAIN}}"
ADMIN_DOMAIN="${MRQ_ADMIN_DOMAIN:-admin.${ROOT_DOMAIN}}"
API_DOMAIN="${MRQ_API_DOMAIN:-api.${ROOT_DOMAIN}}"
DEV_DOMAIN="${MRQ_DEV_DOMAIN:-dev.${ROOT_DOMAIN}}"
PUBLIC_IP="${MRQ_PUBLIC_IP:-}"

ENABLE_NGINX="${MRQ_ENABLE_NGINX:-1}"
SETUP_SSL="${MRQ_SETUP_SSL:-0}"
SSL_EMAIL="${MRQ_SSL_EMAIL:-}"
SSL_DOMAINS="${MRQ_SSL_DOMAINS:-}"

ensure_sudo() {
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi
  echo "[installdev] sudo necessario para instalar dependencias e configurar o Postgres."
  sudo -v
}

ensure_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "[installdev] Comando ausente: $cmd" >&2
    return 1
  fi
  return 0
}

generate_fernet_key() {
  python3 - <<'PY'
import base64
import os
print(base64.urlsafe_b64encode(os.urandom(32)).decode("utf-8"))
PY
}

generate_salt() {
  python3 - <<'PY'
import os
print(os.urandom(32).hex())
PY
}

install_system_packages() {
  ensure_sudo
  sudo apt-get update -y
  sudo apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    dnsutils \
    git \
    libpq-dev \
    nginx \
    certbot \
    python3-certbot-nginx \
    postgresql \
    postgresql-contrib \
    python3 \
    python3-pip \
    python3-venv
}

install_node() {
  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    return 0
  fi

  local nvm_dir="${NVM_DIR:-$HOME/.nvm}"
  if [[ ! -s "$nvm_dir/nvm.sh" ]]; then
    echo "[installdev] Instalando NVM..."
    curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  fi

  # shellcheck disable=SC1090
  source "$nvm_dir/nvm.sh"
  nvm install --lts
  nvm use --lts
}

check_dns() {
  if ! command -v dig >/dev/null 2>&1; then
    echo "[installdev] 'dig' nao disponivel para validar DNS."
    return 0
  fi

  local domains=(
    "$PORTAL_DOMAIN"
    "$CLIENT_DOMAIN"
    "$ADMIN_DOMAIN"
    "$API_DOMAIN"
  )
  echo "[installdev] Validando DNS (A records)..."
  for domain in "${domains[@]}"; do
    local resolved
    resolved="$(dig +short "$domain" | head -n1 | tr -d '\r')"
    if [[ -z "$resolved" ]]; then
      echo " - $domain -> (nao resolvido)"
      continue
    fi
    if [[ -n "$PUBLIC_IP" && "$resolved" != "$PUBLIC_IP" ]]; then
      echo " - $domain -> $resolved (esperado: $PUBLIC_IP)"
    else
      echo " - $domain -> $resolved"
    fi
  done
}

configure_nginx_prod() {
  if [[ "$ENABLE_NGINX" != "1" ]]; then
    return 0
  fi
  ensure_sudo
  MRQ_ROOT_DOMAIN="$ROOT_DOMAIN" \
    MRQ_PORTAL_DOMAIN="$PORTAL_DOMAIN" \
    MRQ_CLIENT_DOMAIN="$CLIENT_DOMAIN" \
    MRQ_ADMIN_DOMAIN="$ADMIN_DOMAIN" \
    MRQ_API_DOMAIN="$API_DOMAIN" \
    bash "$ROOT_DIR/scripts/setup_nginx_prod.sh"
}

setup_ssl_certs() {
  if [[ "$SETUP_SSL" != "1" ]]; then
    return 0
  fi
  if [[ -z "$SSL_EMAIL" ]]; then
    echo "[installdev] MRQ_SSL_EMAIL obrigatorio para configurar certificados." >&2
    exit 1
  fi
  MRQ_ROOT_DOMAIN="$ROOT_DOMAIN" \
    MRQ_PORTAL_DOMAIN="$PORTAL_DOMAIN" \
    MRQ_CLIENT_DOMAIN="$CLIENT_DOMAIN" \
    MRQ_ADMIN_DOMAIN="$ADMIN_DOMAIN" \
    MRQ_API_DOMAIN="$API_DOMAIN" \
    MRQ_SSL_EMAIL="$SSL_EMAIL" \
    MRQ_SSL_DOMAINS="$SSL_DOMAINS" \
    bash "$ROOT_DIR/scripts/ops_ssl_cert.sh"
}

configure_postgres() {
  if [[ -z "$DB_PASS" ]]; then
    read -rsp "Senha para a role do Postgres (${DB_USER}): " DB_PASS
    echo
  fi

  sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${DB_PASS}' CREATEDB;"

  sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_DEV_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE ${DB_DEV_NAME} OWNER ${DB_USER};"

  sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_PROD_NAME}'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE ${DB_PROD_NAME} OWNER ${DB_USER};"
}

write_env_file() {
  local target="$1"
  local db_name="$2"
  local debug="$3"
  local settings_module="$4"
  local encryption_key="$5"
  local hash_salt="$6"

  cp "$ENV_EXAMPLE" "$target"
  sed -i "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://${DB_USER}:${DB_PASS}@localhost:5432/${db_name}|" "$target"
  sed -i "s|^DEBUG=.*|DEBUG=${debug}|" "$target"
  sed -i "s|^DJANGO_SETTINGS_MODULE=.*|DJANGO_SETTINGS_MODULE=${settings_module}|" "$target"
  sed -i "s|^FIELD_ENCRYPTION_KEY=.*|FIELD_ENCRYPTION_KEY=${encryption_key}|" "$target"
  sed -i "s|^FIELD_HASH_SALT=.*|FIELD_HASH_SALT=${hash_salt}|" "$target"
}

configure_envs() {
  if [[ ! -f "$ENV_EXAMPLE" ]]; then
    echo "[installdev] Arquivo nao encontrado: $ENV_EXAMPLE" >&2
    exit 1
  fi

  local dev_key prod_key dev_salt prod_salt
  dev_key="$(generate_fernet_key)"
  prod_key="$(generate_fernet_key)"
  dev_salt="$(generate_salt)"
  prod_salt="$(generate_salt)"

  write_env_file "$ENV_DEV" "$DB_DEV_NAME" "True" "config.settings.dev" "$dev_key" "$dev_salt"
  write_env_file "$ENV_PROD" "$DB_PROD_NAME" "False" "config.settings.prod" "$prod_key" "$prod_salt"

  ln -sf "$(basename "$ENV_DEV")" "$BACKEND_DIR/.env"
}

install_backend_deps() {
  if [[ ! -d "$BACKEND_DIR" ]]; then
    echo "[installdev] Diretorio do backend nao encontrado: $BACKEND_DIR" >&2
    exit 1
  fi

  cd "$BACKEND_DIR"
  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi
  # shellcheck disable=SC1090
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
}

restore_dev_database() {
  if [[ -n "$DEV_DUMP_URL" ]]; then
    local tmp_dump="/tmp/mrquentinha_dev_dump"
    echo "[installdev] Baixando dump dev: $DEV_DUMP_URL"
    curl -fSL "$DEV_DUMP_URL" -o "$tmp_dump"
    DEV_DUMP_PATH="$tmp_dump"
  fi

  if [[ -z "$DEV_DUMP_PATH" ]]; then
    echo "[installdev] Sem dump informado. Aplicando seed DEMO."
    "$ROOT_DIR/scripts/seed_demo.sh"
    return 0
  fi

  echo "[installdev] Restaurando dump em ${DB_DEV_NAME}..."
  if [[ "$DEV_DUMP_PATH" == *.sql ]]; then
    PGPASSWORD="$DB_PASS" psql -U "$DB_USER" -d "$DB_DEV_NAME" -f "$DEV_DUMP_PATH"
  else
    PGPASSWORD="$DB_PASS" pg_restore -U "$DB_USER" -d "$DB_DEV_NAME" --clean --if-exists "$DEV_DUMP_PATH"
  fi
}

prepare_prod_database() {
  echo "[installdev] Preparando banco PROD (vazio, com defaults)..."
  ln -sf "$(basename "$ENV_PROD")" "$BACKEND_DIR/.env"
  (cd "$BACKEND_DIR" && source .venv/bin/activate && python manage.py migrate)
  (cd "$BACKEND_DIR" && source .venv/bin/activate && python manage.py seed_portal_default)
  ln -sf "$(basename "$ENV_DEV")" "$BACKEND_DIR/.env"
}

codex_login_prompt() {
  echo
  echo "[installdev] Configuracao do Codex"
  echo "Escolha o metodo de login:"
  echo "1) Google"
  echo "2) Usuario e senha"
  echo "3) Pular agora"
  read -r -p "Opcao: " login_choice

  mkdir -p "$HOME/.codex"
  case "$login_choice" in
    1)
      echo "google" > "$HOME/.codex/login_method"
      echo "[installdev] Metodo Google selecionado. Execute o login do Codex conforme sua conta."
      ;;
    2)
      echo "password" > "$HOME/.codex/login_method"
      echo "[installdev] Metodo usuario/senha selecionado. Execute o login do Codex conforme sua conta."
      ;;
    *)
      echo "skipped" > "$HOME/.codex/login_method"
      echo "[installdev] Login do Codex ignorado nesta etapa."
      ;;
  esac
}

main() {
  install_system_packages
  install_node
  check_dns
  configure_postgres
  configure_envs
  install_backend_deps
  restore_dev_database
  prepare_prod_database
  configure_nginx_prod
  setup_ssl_certs
  codex_login_prompt

  echo
  echo "[installdev] Ambiente pronto."
  echo "- Backend: scripts/start_backend_dev.sh"
  echo "- Admin:   scripts/start_admin_dev.sh"
  echo "- Portal:  scripts/start_portal_dev.sh"
  echo "- Client:  scripts/start_client_dev.sh"
  echo "- Ops:     scripts/ops_dashboard.sh --auto-start"
  echo
  echo "[installdev] Dicas DNS/SSL (opcional):"
  echo "  MRQ_PUBLIC_IP=<ip-publico> para validar A records."
  echo "  MRQ_ENABLE_NGINX=1 para configurar proxy Nginx."
  echo "  MRQ_SETUP_SSL=1 + MRQ_SSL_EMAIL/MRQ_SSL_DOMAINS para aplicar certificados."
}

main "$@"
