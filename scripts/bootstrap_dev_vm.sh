#!/usr/bin/env bash
set -euo pipefail

info() {
  printf "[INFO] %s\n" "$1"
}

ok() {
  printf "[OK] %s\n" "$1"
}

aviso() {
  printf "[AVISO] %s\n" "$1"
}

erro() {
  printf "[ERRO] %s\n" "$1" >&2
}

verificar_versao_minima() {
  local nome="$1"
  local instalada="$2"
  local requerida="$3"

  if [ "$(printf '%s\n' "$requerida" "$instalada" | sort -V | head -n1)" != "$requerida" ]; then
    erro "$nome abaixo da versao estavel requerida. Instalado: $instalada | Requerido: $requerida"
    exit 1
  fi

  ok "$nome $instalada (>= $requerida)"
}

verificar_ubuntu() {
  if [ ! -f /etc/os-release ]; then
    erro "Arquivo /etc/os-release nao encontrado."
    exit 1
  fi

  . /etc/os-release

  if [ "${ID:-}" != "ubuntu" ] || [ "${VERSION_ID:-}" != "24.04" ]; then
    erro "Este script exige Ubuntu 24.04. Encontrado: ${PRETTY_NAME:-desconhecido}."
    exit 1
  fi

  ok "Ubuntu 24.04 confirmado."
}

obter_versao() {
  local nome="$1"

  case "$nome" in
    git)
      git --version | awk '{print $3}'
      ;;
    python3)
      python3 --version | awk '{print $2}'
      ;;
    node)
      node --version | sed 's/^v//'
      ;;
    psql)
      psql --version | awk '{print $3}'
      ;;
    *)
      erro "Comando '$nome' nao possui extrator de versao definido."
      exit 1
      ;;
  esac
}

verificar_comando() {
  local nome="$1"
  local versao_requerida="$2"

  if ! command -v "$nome" >/dev/null 2>&1; then
    erro "Comando '$nome' nao encontrado."
    exit 1
  fi

  local versao
  versao="$(obter_versao "$nome" 2>/dev/null || true)"

  if [ -z "$versao" ]; then
    erro "Nao foi possivel obter a versao de '$nome'."
    exit 1
  fi

  verificar_versao_minima "$nome" "$versao" "$versao_requerida"
}

criar_estrutura_workspaces() {
  mkdir -p workspaces/backend workspaces/web workspaces/mobile
  ok "Estrutura workspaces garantida."
}

criar_env_example() {
  local env_file="workspaces/backend/.env.example"

  cat <<'ENV' > "$env_file"
DATABASE_URL=postgresql://mrq_user:CHANGE_ME@localhost:5432/mrquentinha
DJANGO_SETTINGS_MODULE=config.settings.dev
DEBUG=True
SECRET_KEY=django-insecure-dev-only-change-me
ALLOWED_HOSTS=127.0.0.1,localhost
ENV

  ok "Arquivo .env.example criado/atualizado em workspaces/backend/.env.example."
}

criar_venv() {
  local venv_dir="workspaces/backend/.venv"

  if [ -d "$venv_dir" ]; then
    ok "Virtualenv ja existe em workspaces/backend/.venv."
    return
  fi

  python3 -m venv "$venv_dir"
  ok "Virtualenv criada em workspaces/backend/.venv."
}

verificar_postgresql_ativo() {
  if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet postgresql; then
    ok "Servico PostgreSQL ativo."
    return 0
  fi

  if command -v pg_isready >/dev/null 2>&1 && pg_isready -q; then
    ok "Servidor PostgreSQL respondendo (pg_isready)."
    return 0
  fi

  info "PostgreSQL nao parece ativo; valide o servico antes de rodar testes."
  return 1
}

obter_database_url() {
  if [ -n "${DATABASE_URL:-}" ]; then
    printf "%s\n" "$DATABASE_URL"
    return 0
  fi

  local env_file="workspaces/backend/.env"
  if [ ! -f "$env_file" ]; then
    return 1
  fi

  local db_url
  db_url="$(grep -E '^DATABASE_URL=' "$env_file" | tail -n1 | cut -d= -f2- || true)"
  db_url="${db_url%\"}"
  db_url="${db_url#\"}"

  if [ -z "$db_url" ]; then
    return 1
  fi

  printf "%s\n" "$db_url"
}

consultar_role_createdb() {
  local role="$1"
  local query
  query="SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='${role}')::int, COALESCE((SELECT rolcreatedb::int FROM pg_roles WHERE rolname='${role}'), 0);"

  local db_url
  db_url="$(obter_database_url || true)"
  if [ -n "$db_url" ]; then
    psql "$db_url" -Atqc "$query" 2>/dev/null && return 0
  fi

  if command -v sudo >/dev/null 2>&1; then
    sudo -n -u postgres psql -d postgres -Atqc "$query" 2>/dev/null && return 0
  fi

  return 1
}

verificar_role_postgres_testes() {
  local role="mrq_user"
  local comando_correcao='sudo -u postgres psql -c "ALTER ROLE mrq_user CREATEDB;"'

  if ! verificar_postgresql_ativo; then
    return 0
  fi

  local resultado
  resultado="$(consultar_role_createdb "$role" || true)"
  if [ -z "$resultado" ]; then
    info "Nao foi possivel verificar automaticamente a role '$role' (sem DATABASE_URL e sem sudo nao interativo)."
    return 0
  fi

  local role_existe
  local role_createdb
  IFS='|' read -r role_existe role_createdb <<< "$resultado"

  if [ "$role_existe" != "1" ] || [ "$role_createdb" != "1" ]; then
    aviso "A role '$role' precisa existir e ter CREATEDB=true para o pytest criar o banco de testes."
    aviso "Corrija com: $comando_correcao"
    return 0
  fi

  ok "Role '$role' com CREATEDB habilitado para testes (pytest)."
}

main() {
  info "Iniciando bootstrap da VM de desenvolvimento."

  local git_requerido="2.30.0"
  local python_requerido="3.11.0"
  local node_requerido="20.0.0" # LTS
  local postgres_requerido="15.0"

  verificar_ubuntu
  verificar_comando git "$git_requerido"
  verificar_comando python3 "$python_requerido"
  verificar_comando node "$node_requerido"
  verificar_comando psql "$postgres_requerido"

  criar_estrutura_workspaces
  criar_env_example
  criar_venv
  verificar_role_postgres_testes

  printf "\nChecklist de validacao (execute manualmente):\n"
  printf -- "- %s\n" "git --version"
  printf -- "- %s\n" "python3 --version"
  printf -- "- %s\n" "node --version"
  printf -- "- %s\n" "psql --version"
  printf -- "- %s\n" "ls -la workspaces"
  printf -- "- %s\n" "cat workspaces/backend/.env.example"
  printf -- "- %s\n" "source workspaces/backend/.venv/bin/activate"
  printf -- "- %s\n" "python --version"
  printf -- "- %s\n" "pytest (requer DATABASE_URL com role CREATEDB)"
}

main "$@"
