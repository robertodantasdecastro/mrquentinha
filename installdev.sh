#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"
ENV_DEV="$BACKEND_DIR/.env.dev"
ENV_PROD="$BACKEND_DIR/.env.prod"

DB_USER="${MRQ_DB_USER:-mrq_user}"
DB_PASS="${MRQ_DB_PASS:-}"
DB_HOST="${MRQ_DB_HOST:-localhost}"
DB_PORT="${MRQ_DB_PORT:-5432}"
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
INSTALL_CLOUDFLARED="${MRQ_INSTALL_CLOUDFLARED:-0}"

INSTALL_FRONTENDS="${MRQ_INSTALL_FRONTENDS:-1}"
BUILD_FRONTENDS="${MRQ_BUILD_FRONTENDS:-1}"
RUN_POST_CHECKS="${MRQ_RUN_POST_CHECKS:-1}"
NON_INTERACTIVE="${MRQ_NON_INTERACTIVE:-1}"
FAIL_ON_DNS_MISMATCH="${MRQ_FAIL_ON_DNS_MISMATCH:-0}"

PRIMARY_IP=""
IS_LOCAL_POSTGRES="0"
AWS_PUBLIC_DNS=""

log() {
  echo "[installdev] $*"
}

warn() {
  echo "[installdev] AVISO: $*" >&2
}

die() {
  echo "[installdev] ERRO: $*" >&2
  exit 1
}

load_secure_machine_secrets() {
  local secure_env_file="${MRQ_SECURE_ENV_FILE:-$HOME/.mrquentinha-secure/host-secrets.env}"
  if [[ -f "$secure_env_file" ]]; then
    # shellcheck disable=SC1090
    source "$secure_env_file"
    log "Segredos locais carregados de: $secure_env_file"
  fi

  if [[ -z "${DB_PASS:-}" && -n "${MRQ_DB_PASS:-}" ]]; then
    DB_PASS="$MRQ_DB_PASS"
  fi
}

ensure_sudo() {
  if sudo -n true >/dev/null 2>&1; then
    return 0
  fi
  log "sudo necessario para instalar dependencias e configurar servicos."
  sudo -v
}

ensure_repo_layout() {
  [[ -d "$BACKEND_DIR" ]] || die "Diretorio do backend nao encontrado: $BACKEND_DIR"
  [[ -f "$ENV_EXAMPLE" ]] || die "Arquivo ausente: $ENV_EXAMPLE"
}

ensure_identifier() {
  local value="$1"
  local label="$2"
  if [[ ! "$value" =~ ^[a-zA-Z_][a-zA-Z0-9_]*$ ]]; then
    die "$label invalido ($value). Use apenas letras, numeros e underscore."
  fi
}

sql_escape_literal() {
  printf "%s" "$1" | sed "s/'/''/g"
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
import secrets
print(secrets.token_hex(32))
PY
}

generate_secret_key() {
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(64))
PY
}

generate_token() {
  python3 - <<'PY'
import secrets
print(secrets.token_hex(24))
PY
}

derive_fernet_key_from_secret() {
  local raw_secret="$1"
  python3 - "$raw_secret" <<'PY'
import base64
import hashlib
import sys
secret = sys.argv[1].encode("utf-8")
digest = hashlib.sha256(secret).digest()
print(base64.urlsafe_b64encode(digest).decode("utf-8"))
PY
}

derive_salt_from_secret() {
  local raw_secret="$1"
  python3 - "$raw_secret" <<'PY'
import hashlib
import sys
secret = sys.argv[1].encode("utf-8")
print(hashlib.sha256(secret).hexdigest())
PY
}

derive_secret_key_from_secret() {
  local raw_secret="$1"
  python3 - "$raw_secret" <<'PY'
import base64
import hashlib
import sys

secret = sys.argv[1].encode("utf-8")
digest = hashlib.sha512(secret).digest()
token = base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")
print(f"mrq-{token}")
PY
}

version_ge() {
  local installed="$1"
  local minimum="$2"
  [[ "$(printf '%s\n' "$minimum" "$installed" | sort -V | head -n1)" == "$minimum" ]]
}

append_unique() {
  local value="$1"
  shift
  local -n target_ref=$1

  if [[ -z "$value" ]]; then
    return 0
  fi

  local item
  for item in "${target_ref[@]}"; do
    if [[ "$item" == "$value" ]]; then
      return 0
    fi
  done
  target_ref+=("$value")
}

join_csv() {
  local values=("$@")
  local joined=""
  local value
  for value in "${values[@]}"; do
    if [[ -z "$value" ]]; then
      continue
    fi
    if [[ -z "$joined" ]]; then
      joined="$value"
    else
      joined="$joined,$value"
    fi
  done
  printf "%s" "$joined"
}

capture_primary_ip() {
  PRIMARY_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"

  local imds_token=""
  imds_token="$(curl -fsS --max-time 2 -X PUT \
    "http://169.254.169.254/latest/api/token" \
    -H "X-aws-ec2-metadata-token-ttl-seconds: 60" 2>/dev/null || true)"

  if [[ -z "${PUBLIC_IP:-}" ]]; then
    if [[ -n "$imds_token" ]]; then
      PUBLIC_IP="$(curl -fsS --max-time 2 \
        -H "X-aws-ec2-metadata-token: ${imds_token}" \
        "http://169.254.169.254/latest/meta-data/public-ipv4" 2>/dev/null || true)"
    fi
    if [[ -z "${PUBLIC_IP:-}" ]]; then
      PUBLIC_IP="$(curl -fsS --max-time 2 https://checkip.amazonaws.com 2>/dev/null | tr -d '\r\n' || true)"
    fi
  fi

  if [[ -n "$imds_token" ]]; then
    AWS_PUBLIC_DNS="$(curl -fsS --max-time 2 \
      -H "X-aws-ec2-metadata-token: ${imds_token}" \
      "http://169.254.169.254/latest/meta-data/public-hostname" 2>/dev/null || true)"
  fi
}

detect_postgres_mode() {
  case "${DB_HOST,,}" in
    localhost|127.0.0.1|::1)
      IS_LOCAL_POSTGRES="1"
      ;;
    *)
      IS_LOCAL_POSTGRES="0"
      ;;
  esac
}

install_system_packages() {
  ensure_sudo
  log "Instalando pacotes base do sistema..."
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    ca-certificates \
    certbot \
    curl \
    dnsutils \
    git \
    jq \
    libpq-dev \
    make \
    nginx \
    postgresql \
    postgresql-client \
    postgresql-contrib \
    python3 \
    python3-certbot-nginx \
    python3-pip \
    python3-venv \
    unzip
}

load_nvm_if_available() {
  local nvm_dir="${NVM_DIR:-$HOME/.nvm}"
  if [[ -s "$nvm_dir/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    source "$nvm_dir/nvm.sh"
    return 0
  fi
  return 1
}

install_node_lts() {
  local needs_install="1"

  if command -v node >/dev/null 2>&1 && command -v npm >/dev/null 2>&1; then
    local node_version
    node_version="$(node --version | sed 's/^v//')"
    if version_ge "$node_version" "20.0.0"; then
      needs_install="0"
      log "Node.js ja instalado (v${node_version})."
    else
      warn "Node.js encontrado, mas abaixo do minimo recomendado (20.x): v${node_version}"
    fi
  fi

  if [[ "$needs_install" == "1" ]]; then
    if ! load_nvm_if_available; then
      log "Instalando NVM para gerenciar Node.js..."
      curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
      load_nvm_if_available || die "Nao foi possivel carregar NVM apos instalacao."
    fi

    log "Instalando Node.js LTS via NVM..."
    nvm install --lts
    nvm alias default 'lts/*'
    nvm use --lts
  fi

  command -v node >/dev/null 2>&1 || die "Node.js nao encontrado apos instalacao."
  command -v npm >/dev/null 2>&1 || die "npm nao encontrado apos instalacao."
  log "Node ativo: $(node --version) | npm: $(npm --version)"
}

validate_dns() {
  if ! command -v dig >/dev/null 2>&1; then
    warn "'dig' indisponivel. Validacao de DNS ignorada."
    return 0
  fi

  local domains=(
    "$PORTAL_DOMAIN"
    "$CLIENT_DOMAIN"
    "$ADMIN_DOMAIN"
    "$API_DOMAIN"
    "$DEV_DOMAIN"
  )

  log "Validando DNS (A records)..."
  local has_error="0"
  local domain
  for domain in "${domains[@]}"; do
    local resolved
    resolved="$(dig +short "$domain" | head -n1 | tr -d '\r')"

    if [[ -z "$resolved" ]]; then
      warn "$domain -> nao resolvido"
      has_error="1"
      continue
    fi

    if [[ -n "$PUBLIC_IP" && "$resolved" != "$PUBLIC_IP" ]]; then
      warn "$domain -> $resolved (esperado: $PUBLIC_IP)"
      has_error="1"
    else
      log "$domain -> $resolved"
    fi
  done

  if [[ "$has_error" == "1" && "$FAIL_ON_DNS_MISMATCH" == "1" ]]; then
    die "DNS divergente e MRQ_FAIL_ON_DNS_MISMATCH=1."
  fi
}

ensure_db_password() {
  if [[ -n "$DB_PASS" ]]; then
    return 0
  fi

  if [[ "$NON_INTERACTIVE" == "1" ]]; then
    DB_PASS="$(generate_token)"
    warn "MRQ_DB_PASS nao informado. Foi gerada senha aleatoria para esta instalacao."
    return 0
  fi

  read -rsp "Senha para a role do Postgres (${DB_USER}): " DB_PASS
  echo
  [[ -n "$DB_PASS" ]] || die "Senha de banco nao pode ser vazia."
}

configure_postgres() {
  ensure_identifier "$DB_USER" "MRQ_DB_USER"
  ensure_identifier "$DB_DEV_NAME" "MRQ_DB_DEV_NAME"
  ensure_identifier "$DB_PROD_NAME" "MRQ_DB_PROD_NAME"

  ensure_db_password
  detect_postgres_mode

  local db_pass_sql
  db_pass_sql="$(sql_escape_literal "$DB_PASS")"

  if [[ "$IS_LOCAL_POSTGRES" == "1" ]]; then
    ensure_sudo
    log "Provisionamento PostgreSQL local habilitado (host=${DB_HOST})."
    sudo systemctl enable --now postgresql

    if sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" | grep -q 1; then
      log "Atualizando role existente (${DB_USER})..."
      sudo -u postgres psql -v ON_ERROR_STOP=1 -c "ALTER ROLE ${DB_USER} WITH LOGIN PASSWORD '${db_pass_sql}' CREATEDB;"
    else
      log "Criando role PostgreSQL (${DB_USER})..."
      sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE ROLE ${DB_USER} WITH LOGIN PASSWORD '${db_pass_sql}' CREATEDB;"
    fi

    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_DEV_NAME}'" | grep -q 1; then
      log "Criando banco DEV (${DB_DEV_NAME})..."
      sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_DEV_NAME} OWNER ${DB_USER};"
    fi

    if ! sudo -u postgres psql -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_PROD_NAME}'" | grep -q 1; then
      log "Criando banco PROD (${DB_PROD_NAME})..."
      sudo -u postgres psql -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_PROD_NAME} OWNER ${DB_USER};"
    fi
    return 0
  fi

  warn "Provisionamento local pulado: MRQ_DB_HOST=${DB_HOST} (PostgreSQL remoto)."
  log "Validando conectividade com PostgreSQL remoto..."
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -c "SELECT 1;" >/dev/null

  if ! PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_DEV_NAME}'" | grep -q 1; then
    log "Criando banco DEV remoto (${DB_DEV_NAME})..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_DEV_NAME};"
  fi

  if ! PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB_PROD_NAME}'" | grep -q 1; then
    log "Criando banco PROD remoto (${DB_PROD_NAME})..."
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE ${DB_PROD_NAME};"
  fi
}

upsert_env() {
  local file_path="$1"
  local key="$2"
  local value="$3"
  local tmp_file

  tmp_file="$(mktemp)"
  awk -v key="$key" -v value="$value" '
    BEGIN { updated = 0 }
    index($0, key "=") == 1 {
      print key "=" value
      updated = 1
      next
    }
    { print }
    END {
      if (updated == 0) {
        print key "=" value
      }
    }
  ' "$file_path" > "$tmp_file"

  mv "$tmp_file" "$file_path"
}

build_allowed_hosts() {
  local env_kind="${1:-dev}"
  local hosts=()
  append_unique "localhost" hosts
  append_unique "127.0.0.1" hosts
  append_unique "$(hostname -f 2>/dev/null || true)" hosts
  append_unique "$(hostname -s 2>/dev/null || true)" hosts
  append_unique "$PRIMARY_IP" hosts
  append_unique "$PUBLIC_IP" hosts
  append_unique "$AWS_PUBLIC_DNS" hosts
  append_unique "$ROOT_DOMAIN" hosts
  append_unique "$PORTAL_DOMAIN" hosts
  append_unique "$CLIENT_DOMAIN" hosts
  append_unique "$ADMIN_DOMAIN" hosts
  append_unique "$API_DOMAIN" hosts
  append_unique "$DEV_DOMAIN" hosts
  if [[ "$env_kind" == "dev" ]]; then
    append_unique ".trycloudflare.com" hosts
  fi
  join_csv "${hosts[@]}"
}

build_web_origins() {
  local env_kind="${1:-dev}"
  local origins=()
  if [[ "$env_kind" == "prod" ]]; then
    local prod_frontend_domains=(
      "$ROOT_DOMAIN"
      "$PORTAL_DOMAIN"
      "$CLIENT_DOMAIN"
      "$ADMIN_DOMAIN"
    )
    local domain
    for domain in "${prod_frontend_domains[@]}"; do
      append_unique "https://${domain}" origins
    done
    join_csv "${origins[@]}"
    return 0
  fi

  local local_hosts=("localhost" "127.0.0.1")
  append_unique "$PRIMARY_IP" local_hosts
  append_unique "$PUBLIC_IP" local_hosts

  local host
  for host in "${local_hosts[@]}"; do
    append_unique "http://${host}:3000" origins
    append_unique "http://${host}:3001" origins
    append_unique "http://${host}:3002" origins
  done

  local frontend_domains=(
    "$PORTAL_DOMAIN"
    "$CLIENT_DOMAIN"
    "$ADMIN_DOMAIN"
    "$DEV_DOMAIN"
  )
  local domain
  for domain in "${frontend_domains[@]}"; do
    append_unique "http://${domain}" origins
    append_unique "https://${domain}" origins
  done

  join_csv "${origins[@]}"
}

build_csrf_origins() {
  local env_kind="${1:-dev}"
  local origins=()
  local base_origins_csv
  base_origins_csv="$(build_web_origins "$env_kind")"
  IFS=',' read -r -a origins <<<"$base_origins_csv"

  if [[ "$env_kind" == "prod" ]]; then
    append_unique "https://${API_DOMAIN}" origins
  else
    append_unique "http://${API_DOMAIN}" origins
    append_unique "https://${API_DOMAIN}" origins
  fi

  join_csv "${origins[@]}"
}

write_env_file() {
  local target="$1"
  local db_name="$2"
  local debug="$3"
  local settings_module="$4"
  local encryption_key="$5"
  local hash_salt="$6"
  local secret_key="$7"
  local webhook_token="$8"

  cp "$ENV_EXAMPLE" "$target"

  local allowed_hosts
  local web_origins
  local csrf_origins
  local env_kind

  if [[ "$debug" == "True" ]]; then
    env_kind="dev"
  else
    env_kind="prod"
  fi

  allowed_hosts="$(build_allowed_hosts "$env_kind")"
  web_origins="$(build_web_origins "$env_kind")"
  csrf_origins="$(build_csrf_origins "$env_kind")"

  upsert_env "$target" "DATABASE_URL" "postgresql://${DB_USER}:${DB_PASS}@${DB_HOST}:${DB_PORT}/${db_name}"
  upsert_env "$target" "DEBUG" "$debug"
  upsert_env "$target" "DJANGO_SETTINGS_MODULE" "$settings_module"
  upsert_env "$target" "SECRET_KEY" "$secret_key"
  upsert_env "$target" "FIELD_ENCRYPTION_KEY" "$encryption_key"
  upsert_env "$target" "FIELD_HASH_SALT" "$hash_salt"
  upsert_env "$target" "FIELD_ENCRYPTION_STRICT" "$([[ "$debug" == "True" ]] && echo "false" || echo "true")"
  upsert_env "$target" "PAYMENTS_WEBHOOK_TOKEN" "$webhook_token"
  upsert_env "$target" "ALLOWED_HOSTS" "$allowed_hosts"
  upsert_env "$target" "CORS_ALLOWED_ORIGINS" "$web_origins"
  upsert_env "$target" "CSRF_TRUSTED_ORIGINS" "$csrf_origins"
}

configure_envs() {
  local dev_key
  local prod_key
  local dev_salt
  local prod_salt
  local dev_secret
  local prod_secret
  local dev_webhook
  local prod_webhook

  if [[ -n "${MRQ_DEFAULT_APP_SECRET:-}" ]]; then
    log "Aplicando segredo padrao da maquina para chaves de aplicacao."
    dev_key="$(derive_fernet_key_from_secret "$MRQ_DEFAULT_APP_SECRET")"
    prod_key="$(derive_fernet_key_from_secret "${MRQ_DEFAULT_APP_SECRET}-prod")"
    dev_salt="$(derive_salt_from_secret "$MRQ_DEFAULT_APP_SECRET")"
    prod_salt="$(derive_salt_from_secret "${MRQ_DEFAULT_APP_SECRET}-prod")"
    dev_secret="$(derive_secret_key_from_secret "${MRQ_DEFAULT_APP_SECRET}-dev")"
    prod_secret="$(derive_secret_key_from_secret "${MRQ_DEFAULT_APP_SECRET}-prod")"
    dev_webhook="$(derive_salt_from_secret "${MRQ_DEFAULT_APP_SECRET}-webhook-dev")"
    prod_webhook="$(derive_salt_from_secret "${MRQ_DEFAULT_APP_SECRET}-webhook-prod")"
  else
    dev_key="$(generate_fernet_key)"
    prod_key="$(generate_fernet_key)"
    dev_salt="$(generate_salt)"
    prod_salt="$(generate_salt)"
    dev_secret="$(generate_secret_key)"
    prod_secret="$(generate_secret_key)"
    dev_webhook="mrq-dev-$(generate_token)"
    prod_webhook="mrq-prod-$(generate_token)"
  fi

  log "Gerando .env.dev e .env.prod..."
  write_env_file "$ENV_DEV" "$DB_DEV_NAME" "True" "config.settings.dev" "$dev_key" "$dev_salt" "$dev_secret" "$dev_webhook"
  write_env_file "$ENV_PROD" "$DB_PROD_NAME" "False" "config.settings.prod" "$prod_key" "$prod_salt" "$prod_secret" "$prod_webhook"

  ln -sfn "$(basename "$ENV_DEV")" "$BACKEND_DIR/.env"
}

activate_backend_venv() {
  # shellcheck disable=SC1090
  source "$BACKEND_DIR/.venv/bin/activate"
}

install_backend_deps() {
  log "Instalando dependencias Python do backend..."
  cd "$BACKEND_DIR"
  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi

  activate_backend_venv
  pip install --upgrade pip setuptools wheel
  pip install -r requirements-dev.txt
}

run_manage() {
  local env_file="$1"
  shift

  (
    cd "$BACKEND_DIR"
    ln -sfn "$(basename "$env_file")" .env
    activate_backend_venv
    "$@"
  )
}

recreate_dev_database() {
  detect_postgres_mode
  if [[ "$IS_LOCAL_POSTGRES" == "1" ]]; then
    ensure_sudo
    log "Recriando banco DEV local (${DB_DEV_NAME}) para restauracao limpa..."
    sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '${DB_DEV_NAME}' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS ${DB_DEV_NAME};
CREATE DATABASE ${DB_DEV_NAME} OWNER ${DB_USER};
SQL
    return 0
  fi

  log "Recriando banco DEV remoto (${DB_DEV_NAME}) para restauracao limpa..."
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres -v ON_ERROR_STOP=1 <<SQL
DROP DATABASE IF EXISTS ${DB_DEV_NAME};
CREATE DATABASE ${DB_DEV_NAME};
SQL
}

restore_dev_database() {
  if [[ -n "$DEV_DUMP_URL" ]]; then
    local tmp_dump
    tmp_dump="/tmp/mrquentinha_dev_dump_$(date +%s)"
    log "Baixando dump DEV: $DEV_DUMP_URL"
    curl -fSL "$DEV_DUMP_URL" -o "$tmp_dump"
    DEV_DUMP_PATH="$tmp_dump"
  fi

  if [[ -z "$DEV_DUMP_PATH" ]]; then
    log "Sem dump DEV informado. Aplicando migrate + seed_demo no DEV."
    run_manage "$ENV_DEV" python manage.py migrate --noinput
    run_manage "$ENV_DEV" python manage.py seed_demo
    run_manage "$ENV_DEV" python manage.py seed_portal_default
    return 0
  fi

  [[ -f "$DEV_DUMP_PATH" ]] || die "Dump DEV nao encontrado: $DEV_DUMP_PATH"

  recreate_dev_database

  log "Restaurando dump DEV em ${DB_DEV_NAME}..."
  if [[ "$DEV_DUMP_PATH" == *.sql ]]; then
    PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_DEV_NAME" -v ON_ERROR_STOP=1 -f "$DEV_DUMP_PATH"
  else
    PGPASSWORD="$DB_PASS" pg_restore \
      -h "$DB_HOST" \
      -p "$DB_PORT" \
      -U "$DB_USER" \
      -d "$DB_DEV_NAME" \
      --clean \
      --if-exists \
      --no-owner \
      --no-privileges \
      "$DEV_DUMP_PATH"
  fi

  run_manage "$ENV_DEV" python manage.py migrate --noinput
  run_manage "$ENV_DEV" python manage.py seed_portal_default
}

prepare_prod_database() {
  log "Preparando banco PROD (migrate + seed_portal_default)..."
  run_manage "$ENV_PROD" python manage.py migrate --noinput
  run_manage "$ENV_PROD" python manage.py seed_portal_default
}

install_frontend_deps() {
  if [[ "$INSTALL_FRONTENDS" != "1" ]]; then
    log "Instalacao de dependencias frontend desabilitada (MRQ_INSTALL_FRONTENDS=0)."
    return 0
  fi

  log "Instalando dependencias frontend (ui/admin/portal/client)..."

  local projects=(
    "$ROOT_DIR/workspaces/web/ui"
    "$ROOT_DIR/workspaces/web/admin"
    "$ROOT_DIR/workspaces/web/portal"
    "$ROOT_DIR/workspaces/web/client"
  )

  local project
  for project in "${projects[@]}"; do
    [[ -d "$project" ]] || die "Diretorio frontend nao encontrado: $project"
    if [[ -f "$project/package-lock.json" ]]; then
      (cd "$project" && npm ci --no-audit --fund=false)
    else
      (cd "$project" && npm install)
    fi
  done
}

build_frontends() {
  if [[ "$INSTALL_FRONTENDS" != "1" || "$BUILD_FRONTENDS" != "1" ]]; then
    log "Build frontend desabilitado (MRQ_BUILD_FRONTENDS=0 ou install frontend desligado)."
    return 0
  fi

  log "Gerando build de producao dos frontends web..."
  (cd "$ROOT_DIR/workspaces/web/admin" && npm run build)
  (cd "$ROOT_DIR/workspaces/web/portal" && npm run build)
  (cd "$ROOT_DIR/workspaces/web/client" && npm run build)
}

configure_nginx_prod() {
  if [[ "$ENABLE_NGINX" != "1" ]]; then
    log "Configuracao do Nginx desabilitada (MRQ_ENABLE_NGINX=0)."
    return 0
  fi

  log "Aplicando configuracao Nginx para subdominios..."
  MRQ_ROOT_DOMAIN="$ROOT_DOMAIN" \
  MRQ_PORTAL_DOMAIN="$PORTAL_DOMAIN" \
  MRQ_CLIENT_DOMAIN="$CLIENT_DOMAIN" \
  MRQ_ADMIN_DOMAIN="$ADMIN_DOMAIN" \
  MRQ_API_DOMAIN="$API_DOMAIN" \
  MRQ_MOBILE_API_PUBLIC_IP="$PUBLIC_IP" \
  MRQ_MOBILE_API_AWS_DNS="$AWS_PUBLIC_DNS" \
    bash "$ROOT_DIR/scripts/setup_nginx_prod.sh"
}

setup_ssl_certs() {
  if [[ "$SETUP_SSL" != "1" ]]; then
    log "SSL/TLS desabilitado (MRQ_SETUP_SSL=0)."
    return 0
  fi

  [[ -n "$SSL_EMAIL" ]] || die "MRQ_SSL_EMAIL obrigatorio quando MRQ_SETUP_SSL=1."

  log "Aplicando certificados SSL/TLS via certbot..."
  MRQ_ROOT_DOMAIN="$ROOT_DOMAIN" \
    MRQ_PORTAL_DOMAIN="$PORTAL_DOMAIN" \
    MRQ_CLIENT_DOMAIN="$CLIENT_DOMAIN" \
    MRQ_ADMIN_DOMAIN="$ADMIN_DOMAIN" \
    MRQ_API_DOMAIN="$API_DOMAIN" \
    MRQ_SSL_EMAIL="$SSL_EMAIL" \
    MRQ_SSL_DOMAINS="$SSL_DOMAINS" \
    bash "$ROOT_DIR/scripts/ops_ssl_cert.sh"
}

install_cloudflared_if_requested() {
  if [[ "$INSTALL_CLOUDFLARED" != "1" ]]; then
    return 0
  fi

  log "Instalando cloudflared local (modo DEV online/hibrido)..."
  bash "$ROOT_DIR/scripts/install_cloudflared_local.sh"
}

run_post_checks() {
  if [[ "$RUN_POST_CHECKS" != "1" ]]; then
    log "Post-checks desabilitados (MRQ_RUN_POST_CHECKS=0)."
    return 0
  fi

  log "Executando validacoes pos-instalacao..."
  run_manage "$ENV_DEV" python manage.py check
  run_manage "$ENV_PROD" python manage.py check

  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_DEV_NAME" -c "SELECT 1;" >/dev/null
  PGPASSWORD="$DB_PASS" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_PROD_NAME" -c "SELECT 1;" >/dev/null

  ln -sfn "$(basename "$ENV_DEV")" "$BACKEND_DIR/.env"
  log "Post-checks concluidos."
}

print_summary() {
  log "Ambiente preparado com sucesso."
  echo
  echo "Arquivos de ambiente:"
  echo "- $ENV_DEV"
  echo "- $ENV_PROD"
  echo "- $BACKEND_DIR/.env -> $(readlink "$BACKEND_DIR/.env" 2>/dev/null || echo '.env.dev')"
  echo
  echo "Bancos PostgreSQL:"
  echo "- DEV:  ${DB_DEV_NAME}"
  echo "- PROD: ${DB_PROD_NAME}"
  echo
  echo "Comandos operacionais:"
  echo "- Backend DEV: ./scripts/start_backend_dev.sh"
  echo "- Admin DEV:   ./scripts/start_admin_dev.sh"
  echo "- Portal DEV:  ./scripts/start_portal_dev.sh"
  echo "- Client DEV:  ./scripts/start_client_dev.sh"
  echo "- Stack PROD:  ./scripts/start_vm_prod.sh"
  echo "- Ops:         ./scripts/ops_dashboard.sh --auto-start"
  echo
  echo "Opcao de smoke completo (recomendado):"
  echo "- VM_IP=${PRIMARY_IP:-127.0.0.1} ./scripts/smoke_stack_dev.sh"
}

main() {
  ensure_repo_layout
  load_secure_machine_secrets
  capture_primary_ip

  install_system_packages
  install_node_lts
  validate_dns
  configure_postgres
  configure_envs
  install_backend_deps
  restore_dev_database
  prepare_prod_database
  install_frontend_deps
  build_frontends
  configure_nginx_prod
  setup_ssl_certs
  install_cloudflared_if_requested
  run_post_checks
  print_summary
}

main "$@"
