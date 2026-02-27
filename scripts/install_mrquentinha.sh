#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"
INSTALL_STATE_DIR="$ROOT_DIR/.runtime/install"
PROFILE_FILE="$INSTALL_STATE_DIR/install_profile.env"

TARGET_USER="${SUDO_USER:-$USER}"
STACK_MODEL=""
APP_ENV=""
AUTO_YES="0"
START_AFTER_INSTALL="0"

VM_DB_NAME="mrquentinha"
VM_DB_USER="mrq_user"
VM_DB_PASS="mrq_vm_change_me"

COLOR_RESET="\033[0m"
COLOR_TITLE="\033[1;36m"
COLOR_INFO="\033[1;34m"
COLOR_OK="\033[1;32m"
COLOR_WARN="\033[1;33m"
COLOR_ERR="\033[1;31m"

info() { printf "%b[INFO]%b %s\n" "$COLOR_INFO" "$COLOR_RESET" "$1"; }
ok() { printf "%b[OK]%b %s\n" "$COLOR_OK" "$COLOR_RESET" "$1"; }
warn() { printf "%b[AVISO]%b %s\n" "$COLOR_WARN" "$COLOR_RESET" "$1"; }
err() { printf "%b[ERRO]%b %s\n" "$COLOR_ERR" "$COLOR_RESET" "$1" >&2; }

step_counter=0
TOTAL_STEPS=11
step() {
  step_counter=$((step_counter + 1))
  printf "\n%b========== [%d/%d] %s ==========%b\n" "$COLOR_TITLE" "$step_counter" "$TOTAL_STEPS" "$1" "$COLOR_RESET"
}

usage() {
  cat <<TXT
Instalador Mr Quentinha (Ubuntu)

Uso:
  bash scripts/install_mrquentinha.sh [opcoes]

Opcoes:
  --stack vm|docker     Modelo de execucao.
  --env dev|prod        Ambiente alvo.
  --yes                 Nao faz perguntas de confirmacao.
  --start               Inicia os servicos ao final.
  -h, --help            Exibe esta ajuda.
TXT
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stack)
      STACK_MODEL="${2:-}"
      shift 2
      ;;
    --env)
      APP_ENV="${2:-}"
      shift 2
      ;;
    --yes)
      AUTO_YES="1"
      shift
      ;;
    --start)
      START_AFTER_INSTALL="1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      err "Opcao invalida: $1"
      usage
      exit 1
      ;;
  esac
done

run_root() {
  if [[ "$(id -u)" -eq 0 ]]; then
    bash -lc "$*"
  else
    sudo bash -lc "$*"
  fi
}

version_ge() {
  local installed="$1"
  local minimum="$2"
  [[ "$(printf '%s\n' "$minimum" "$installed" | sort -V | head -n1)" == "$minimum" ]]
}

require_ubuntu() {
  if [[ ! -f /etc/os-release ]]; then
    err "Nao foi possivel identificar o sistema operacional."
    exit 1
  fi

  # shellcheck disable=SC1091
  source /etc/os-release
  if [[ "${ID:-}" != "ubuntu" ]]; then
    err "Este instalador foi desenhado para Ubuntu. Encontrado: ${PRETTY_NAME:-desconhecido}"
    exit 1
  fi

  ok "Sistema operacional detectado: ${PRETTY_NAME:-Ubuntu}"
}

prompt_with_default() {
  local label="$1"
  local default_value="$2"
  local output_var="$3"

  if [[ "$AUTO_YES" == "1" ]]; then
    printf -v "$output_var" "%s" "$default_value"
    return
  fi

  printf "%s [%s]: " "$label" "$default_value"
  read -r user_value
  if [[ -z "${user_value:-}" ]]; then
    printf -v "$output_var" "%s" "$default_value"
  else
    printf -v "$output_var" "%s" "$user_value"
  fi
}

ask_yes_no() {
  local label="$1"
  local default_value="${2:-y}"

  if [[ "$AUTO_YES" == "1" ]]; then
    [[ "$default_value" == "y" ]] && return 0 || return 1
  fi

  local prompt_suffix="[Y/n]"
  [[ "$default_value" == "n" ]] && prompt_suffix="[y/N]"

  printf "%s %s " "$label" "$prompt_suffix"
  read -r answer

  if [[ -z "${answer:-}" ]]; then
    answer="$default_value"
  fi

  case "${answer,,}" in
    y|yes|s|sim) return 0 ;;
    n|no|nao) return 1 ;;
    *)
      warn "Resposta invalida. Assumindo padrao: $default_value"
      [[ "$default_value" == "y" ]] && return 0 || return 1
      ;;
  esac
}

select_stack_model() {
  if [[ "$STACK_MODEL" == "vm" || "$STACK_MODEL" == "docker" ]]; then
    return
  fi

  if [[ "$AUTO_YES" == "1" ]]; then
    STACK_MODEL="vm"
    return
  fi

  printf "\nSelecione o modelo de execucao:\n"
  printf "  1) VM (arquitetura atual, sem Docker)\n"
  printf "  2) Docker (nova estrutura containerizada)\n"
  printf "Escolha [1-2] (padrao: 1): "
  read -r option
  case "${option:-1}" in
    2) STACK_MODEL="docker" ;;
    *) STACK_MODEL="vm" ;;
  esac
}

select_app_env() {
  if [[ "$APP_ENV" == "dev" || "$APP_ENV" == "prod" ]]; then
    return
  fi

  if [[ "$AUTO_YES" == "1" ]]; then
    APP_ENV="dev"
    return
  fi

  printf "\nSelecione o ambiente:\n"
  printf "  1) Desenvolvimento (dev)\n"
  printf "  2) Producao (prod)\n"
  printf "Escolha [1-2] (padrao: 1): "
  read -r option
  case "${option:-1}" in
    2) APP_ENV="prod" ;;
    *) APP_ENV="dev" ;;
  esac
}

install_base_packages() {
  info "Instalando pacotes base do sistema..."
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get update -y"
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get install -y \
    ca-certificates curl gnupg lsb-release jq make unzip git software-properties-common"
  ok "Pacotes base instalados."
}

ensure_node_lts() {
  if command -v node >/dev/null 2>&1; then
    local node_version
    node_version="$(node --version | sed 's/^v//')"
    if version_ge "$node_version" "20.0.0"; then
      ok "Node.js ja instalado: v$node_version"
      return
    fi
    warn "Node.js encontrado, mas abaixo do minimo recomendado (20.x)."
  fi

  info "Instalando Node.js LTS (20.x)..."
  run_root "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -"
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get install -y nodejs"
  ok "Node.js instalado: $(node --version 2>/dev/null || echo 'validar manualmente')"
}

ensure_vm_packages() {
  info "Instalando dependencias VM (Python, PostgreSQL, Nginx)..."
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get install -y \
    python3 python3-venv python3-pip python3-dev build-essential libpq-dev \
    postgresql postgresql-contrib nginx"

  run_root "systemctl enable --now postgresql || true"
  ok "Dependencias VM instaladas."
}

configure_vm_postgres() {
  if [[ "$AUTO_YES" != "1" ]]; then
    prompt_with_default "Nome do banco PostgreSQL" "$VM_DB_NAME" VM_DB_NAME
    prompt_with_default "Usuario PostgreSQL" "$VM_DB_USER" VM_DB_USER
    prompt_with_default "Senha do usuario PostgreSQL" "$VM_DB_PASS" VM_DB_PASS
  fi

  info "Configurando banco PostgreSQL local..."

  if [[ "$(id -u)" -eq 0 ]]; then
    runuser -u postgres -- psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${VM_DB_USER}'" | grep -q 1 \
      || runuser -u postgres -- psql -c "CREATE ROLE ${VM_DB_USER} WITH LOGIN PASSWORD '${VM_DB_PASS}' CREATEDB;"

    runuser -u postgres -- psql -tc "SELECT 1 FROM pg_database WHERE datname='${VM_DB_NAME}'" | grep -q 1 \
      || runuser -u postgres -- psql -c "CREATE DATABASE ${VM_DB_NAME} OWNER ${VM_DB_USER};"

    runuser -u postgres -- psql -c "ALTER ROLE ${VM_DB_USER} WITH CREATEDB;" >/dev/null
  else
    sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${VM_DB_USER}'" | grep -q 1 \
      || sudo -u postgres psql -c "CREATE ROLE ${VM_DB_USER} WITH LOGIN PASSWORD '${VM_DB_PASS}' CREATEDB;"

    sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${VM_DB_NAME}'" | grep -q 1 \
      || sudo -u postgres psql -c "CREATE DATABASE ${VM_DB_NAME} OWNER ${VM_DB_USER};"

    sudo -u postgres psql -c "ALTER ROLE ${VM_DB_USER} WITH CREATEDB;" >/dev/null
  fi

  ok "PostgreSQL configurado (db=${VM_DB_NAME}, user=${VM_DB_USER})."
}

upsert_env() {
  local key="$1"
  local value="$2"
  local file="$3"

  if grep -q "^${key}=" "$file"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$file"
  else
    printf "%s=%s\n" "$key" "$value" >> "$file"
  fi
}

configure_backend_env_vm() {
  local env_file="$BACKEND_DIR/.env"
  local settings_module="config.settings.dev"
  local debug_value="True"

  if [[ "$APP_ENV" == "prod" ]]; then
    settings_module="config.settings.prod"
    debug_value="False"
  fi

  if [[ ! -f "$env_file" ]]; then
    cp "$BACKEND_DIR/.env.example" "$env_file"
    info "Arquivo .env criado a partir de .env.example"
  else
    warn "Arquivo .env ja existe. Sera ajustado com valores essenciais."
  fi

  local db_url="postgresql://${VM_DB_USER}:${VM_DB_PASS}@localhost:5432/${VM_DB_NAME}"
  upsert_env "DATABASE_URL" "$db_url" "$env_file"
  upsert_env "DJANGO_SETTINGS_MODULE" "$settings_module" "$env_file"
  upsert_env "DEBUG" "$debug_value" "$env_file"
  upsert_env "SECRET_KEY" "django-insecure-${APP_ENV}-change-me" "$env_file"
  upsert_env "ALLOWED_HOSTS" "localhost,127.0.0.1,10.211.55.21" "$env_file"
  upsert_env "PAYMENTS_WEBHOOK_TOKEN" "mrq-${APP_ENV}-webhook-token" "$env_file"

  if [[ "$APP_ENV" == "dev" ]]; then
    upsert_env "CORS_ALLOWED_ORIGINS" "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002" "$env_file"
    upsert_env "CSRF_TRUSTED_ORIGINS" "http://localhost:3000,http://localhost:3001,http://localhost:3002,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:3002" "$env_file"
  fi

  ok "Backend .env configurado para $APP_ENV."
}

install_backend_vm() {
  info "Configurando backend Python..."
  cd "$BACKEND_DIR"

  if [[ ! -d .venv ]]; then
    python3 -m venv .venv
  fi

  # shellcheck disable=SC1091
  source .venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements-dev.txt
  python manage.py migrate --noinput

  if [[ "$APP_ENV" == "prod" ]]; then
    python manage.py collectstatic --noinput
  fi

  python manage.py check
  deactivate
  ok "Backend pronto."
}

install_frontend_stack_vm() {
  info "Instalando dependencias Node (UI, Admin, Portal, Client)..."

  local projects=(
    "$ROOT_DIR/workspaces/web/ui"
    "$ROOT_DIR/workspaces/web/admin"
    "$ROOT_DIR/workspaces/web/portal"
    "$ROOT_DIR/workspaces/web/client"
  )

  for project in "${projects[@]}"; do
    info "npm install em ${project#$ROOT_DIR/}"
    (cd "$project" && npm ci || npm install)
  done

  if [[ "$APP_ENV" == "prod" ]]; then
    info "Gerando build dos frontends para producao..."
    (cd "$ROOT_DIR/workspaces/web/admin" && npm run build)
    (cd "$ROOT_DIR/workspaces/web/portal" && npm run build)
    (cd "$ROOT_DIR/workspaces/web/client" && npm run build)
  fi

  ok "Frontends preparados."
}

ensure_docker_engine() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    ok "Docker + Compose ja instalados."
    return
  fi

  info "Instalando Docker Engine + Docker Compose plugin..."
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get install -y ca-certificates curl gnupg"
  run_root "install -m 0755 -d /etc/apt/keyrings"
  run_root "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg"
  run_root "chmod a+r /etc/apt/keyrings/docker.gpg"
  run_root "echo \"deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo \$VERSION_CODENAME) stable\" > /etc/apt/sources.list.d/docker.list"
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get update -y"
  run_root "export DEBIAN_FRONTEND=noninteractive; apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin"

  if [[ -n "$TARGET_USER" ]]; then
    run_root "usermod -aG docker '$TARGET_USER' || true"
  fi

  run_root "systemctl enable --now docker || true"
  ok "Docker instalado."
}

prepare_docker_env() {
  local env_file="$ROOT_DIR/docker/.env.${APP_ENV}"
  local env_example="$ROOT_DIR/docker/.env.${APP_ENV}.example"

  if [[ ! -f "$env_example" ]]; then
    err "Arquivo de exemplo nao encontrado: $env_example"
    exit 1
  fi

  if [[ ! -f "$env_file" ]]; then
    cp "$env_example" "$env_file"
    ok "Arquivo criado: docker/.env.${APP_ENV}"
  else
    warn "Arquivo ja existe: docker/.env.${APP_ENV} (mantido)"
  fi
}

build_docker_stack() {
  info "Construindo stack Docker ($APP_ENV)..."
  bash "$ROOT_DIR/scripts/docker_lifecycle.sh" "$APP_ENV" build
  ok "Build Docker concluido."
}

persist_install_profile() {
  mkdir -p "$INSTALL_STATE_DIR"
  cat > "$PROFILE_FILE" <<PROFILE
MRQ_STACK_MODEL=$STACK_MODEL
MRQ_STACK_ENV=$APP_ENV
MRQ_INSTALLED_AT=$(date -Iseconds)
PROFILE
  ok "Perfil de instalacao salvo em ${PROFILE_FILE#$ROOT_DIR/}"
}

start_stack_if_requested() {
  if [[ "$START_AFTER_INSTALL" != "1" ]]; then
    return
  fi

  if [[ "$STACK_MODEL" == "docker" ]]; then
    info "Iniciando stack Docker ($APP_ENV)..."
    bash "$ROOT_DIR/scripts/docker_lifecycle.sh" "$APP_ENV" up
    return
  fi

  if [[ "$APP_ENV" == "prod" ]]; then
    info "Iniciando stack VM em modo producao..."
    bash "$ROOT_DIR/scripts/start_vm_prod.sh"
    return
  fi

  info "Abrindo Ops Dashboard em modo dev com auto-start..."
  bash "$ROOT_DIR/scripts/ops_dashboard.sh" --auto-start
}

print_summary() {
  printf "\n%b=========== INSTALACAO CONCLUIDA ===========%b\n" "$COLOR_TITLE" "$COLOR_RESET"
  printf "Modelo : %s\n" "$STACK_MODEL"
  printf "Ambiente: %s\n" "$APP_ENV"

  if [[ "$STACK_MODEL" == "vm" ]]; then
    cat <<TXT

Comandos principais (VM):
- Dev:  bash scripts/ops_dashboard.sh --auto-start
- Prod: bash scripts/start_vm_prod.sh
- Stop prod: bash scripts/stop_vm_prod.sh
- Proxy local opcional: bash scripts/start_proxy_dev.sh
TXT
  else
    cat <<TXT

Comandos principais (Docker):
- Start:  bash scripts/docker_lifecycle.sh $APP_ENV up
- Status: bash scripts/docker_lifecycle.sh $APP_ENV ps
- Logs:   bash scripts/docker_lifecycle.sh $APP_ENV logs
- Stop:   bash scripts/docker_lifecycle.sh $APP_ENV down
TXT

    if [[ "$TARGET_USER" == "$USER" ]]; then
      warn "Pode ser necessario abrir nova sessao para refletir grupo docker (newgrp docker)."
    fi
  fi

  cat <<TXT

Quality gate completo:
- bash scripts/quality_gate_all.sh
TXT
}

main() {
  step "Validacoes iniciais"
  require_ubuntu

  select_stack_model
  select_app_env

  info "Selecao atual: modelo=$STACK_MODEL | ambiente=$APP_ENV"

  if ! ask_yes_no "Deseja continuar com a instalacao?" "y"; then
    warn "Instalacao cancelada pelo usuario."
    exit 0
  fi

  step "Instalando pacotes base"
  install_base_packages

  step "Instalando Node.js LTS"
  ensure_node_lts

  if [[ "$STACK_MODEL" == "vm" ]]; then
    step "Instalando dependencias VM"
    ensure_vm_packages

    step "Configurando PostgreSQL local"
    configure_vm_postgres

    step "Configurando .env do backend"
    configure_backend_env_vm

    step "Instalando backend Python"
    install_backend_vm

    step "Instalando frontends web"
    install_frontend_stack_vm
  else
    step "Instalando Docker Engine"
    ensure_docker_engine

    step "Preparando arquivos de ambiente Docker"
    prepare_docker_env

    step "Build da stack Docker"
    build_docker_stack
  fi

  step "Persistindo perfil de instalacao"
  persist_install_profile

  step "Inicializacao opcional"
  start_stack_if_requested

  step "Resumo final"
  print_summary
}

main "$@"
