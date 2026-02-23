#!/usr/bin/env bash
set -euo pipefail

info() {
  printf "[INFO] %s\n" "$1"
}

ok() {
  printf "[OK] %s\n" "$1"
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

  printf "\nChecklist de validacao (execute manualmente):\n"
  printf -- "- %s\n" "git --version"
  printf -- "- %s\n" "python3 --version"
  printf -- "- %s\n" "node --version"
  printf -- "- %s\n" "psql --version"
  printf -- "- %s\n" "ls -la workspaces"
  printf -- "- %s\n" "cat workspaces/backend/.env.example"
  printf -- "- %s\n" "source workspaces/backend/.venv/bin/activate"
  printf -- "- %s\n" "python --version"
}

main "$@"
