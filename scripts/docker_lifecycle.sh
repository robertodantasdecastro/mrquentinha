#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOCKER_DIR="$ROOT_DIR/docker"

COLOR_RESET="\033[0m"
COLOR_INFO="\033[1;34m"
COLOR_OK="\033[1;32m"
COLOR_WARN="\033[1;33m"
COLOR_ERR="\033[1;31m"

info() { printf "%b[INFO]%b %s\n" "$COLOR_INFO" "$COLOR_RESET" "$1"; }
ok() { printf "%b[OK]%b %s\n" "$COLOR_OK" "$COLOR_RESET" "$1"; }
warn() { printf "%b[AVISO]%b %s\n" "$COLOR_WARN" "$COLOR_RESET" "$1"; }
err() { printf "%b[ERRO]%b %s\n" "$COLOR_ERR" "$COLOR_RESET" "$1" >&2; }

ensure_docker() {
  if ! command -v docker >/dev/null 2>&1; then
    err "Docker nao encontrado no PATH."
    exit 1
  fi

  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return 0
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return 0
  fi

  err "Docker Compose nao encontrado (docker compose ou docker-compose)."
  exit 1
}

resolve_defaults_from_profile() {
  local profile_file="$ROOT_DIR/.runtime/install/install_profile.env"
  if [[ -f "$profile_file" ]]; then
    # shellcheck disable=SC1090
    source "$profile_file"
    DEFAULT_STACK_MODEL="${MRQ_STACK_MODEL:-docker}"
    DEFAULT_STACK_ENV="${MRQ_STACK_ENV:-dev}"
  else
    DEFAULT_STACK_MODEL="docker"
    DEFAULT_STACK_ENV="dev"
  fi
}

select_mode_interactive() {
  printf "\n"
  info "Selecione o ambiente Docker"
  printf "  1) Desenvolvimento (docker-compose.dev.yml)\n"
  printf "  2) Producao (docker-compose.prod.yml)\n"
  printf "  Escolha [1-2] (padrao: %s): " "$DEFAULT_STACK_ENV"
  read -r opt
  case "${opt:-}" in
    2) STACK_ENV="prod" ;;
    1) STACK_ENV="dev" ;;
    "") STACK_ENV="$DEFAULT_STACK_ENV" ;;
    *)
      warn "Opcao invalida. Usando padrao: $DEFAULT_STACK_ENV"
      STACK_ENV="$DEFAULT_STACK_ENV"
      ;;
  esac
}

select_action_interactive() {
  printf "\n"
  info "Acoes disponiveis"
  printf "  1) up\n"
  printf "  2) down\n"
  printf "  3) restart\n"
  printf "  4) logs\n"
  printf "  5) ps\n"
  printf "  6) build\n"
  printf "  Escolha [1-6] (padrao: ps): "
  read -r opt
  case "${opt:-}" in
    1) ACTION="up" ;;
    2) ACTION="down" ;;
    3) ACTION="restart" ;;
    4) ACTION="logs" ;;
    5|"") ACTION="ps" ;;
    6) ACTION="build" ;;
    *)
      warn "Opcao invalida. Usando ps."
      ACTION="ps"
      ;;
  esac
}

compose_files_for_env() {
  case "$STACK_ENV" in
    dev)
      COMPOSE_FILE="$DOCKER_DIR/docker-compose.dev.yml"
      ENV_FILE="$DOCKER_DIR/.env.dev"
      ;;
    prod)
      COMPOSE_FILE="$DOCKER_DIR/docker-compose.prod.yml"
      ENV_FILE="$DOCKER_DIR/.env.prod"
      ;;
    *)
      err "Ambiente invalido: $STACK_ENV (use dev|prod)."
      exit 1
      ;;
  esac

  if [[ ! -f "$COMPOSE_FILE" ]]; then
    err "Compose file nao encontrado: $COMPOSE_FILE"
    exit 1
  fi

  if [[ ! -f "$ENV_FILE" ]]; then
    warn "Arquivo $ENV_FILE nao encontrado."
    warn "Copie a partir do exemplo correspondente em docker/.env.$STACK_ENV.example"
    exit 1
  fi
}

run_compose() {
  (
    cd "$DOCKER_DIR"
    "${COMPOSE_CMD[@]}" --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
  )
}

show_urls() {
  if [[ "$STACK_ENV" = "dev" ]]; then
    cat <<TXT

URLs dev esperadas:
- Backend: http://127.0.0.1:8000
- Portal:  http://127.0.0.1:3000
- Client:  http://127.0.0.1:3001
- Admin:   http://127.0.0.1:3002
- Proxy:   http://127.0.0.1:8088
TXT
    return
  fi

  cat <<TXT

URLs prod esperadas (ajuste DNS):
- API:    http://api.mrquentinha.com.br
- Portal: http://www.mrquentinha.com.br
- Client: http://app.mrquentinha.com.br
- Admin:  http://admin.mrquentinha.com.br
TXT
}

main() {
  ensure_docker
  resolve_defaults_from_profile

  STACK_ENV="${1:-}"
  ACTION="${2:-}"

  if [[ -z "$STACK_ENV" ]]; then
    select_mode_interactive
  fi

  if [[ -z "$ACTION" ]]; then
    select_action_interactive
  fi

  compose_files_for_env

  info "Docker lifecycle | ambiente=$STACK_ENV | acao=$ACTION"
  case "$ACTION" in
    up)
      run_compose up -d --build
      ok "Stack iniciada."
      show_urls
      ;;
    down)
      run_compose down
      ok "Stack parada."
      ;;
    restart)
      run_compose down
      run_compose up -d --build
      ok "Stack reiniciada."
      show_urls
      ;;
    logs)
      run_compose logs -f --tail 200
      ;;
    ps|status)
      run_compose ps
      ;;
    build)
      run_compose build
      ok "Build concluido."
      ;;
    *)
      err "Acao invalida: $ACTION (use up|down|restart|logs|ps|build)."
      exit 1
      ;;
  esac
}

main "$@"
