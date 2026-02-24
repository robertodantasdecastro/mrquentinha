#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

activate_backend_venv() {
  if [[ -f "$ROOT_DIR/workspaces/backend/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "$ROOT_DIR/workspaces/backend/.venv/bin/activate"
  fi
}

show_workflow() {
  local workflow_file="$1"
  echo "[session] Workflow: $workflow_file"
  echo
  sed -n '1,120p' "$ROOT_DIR/.agent/workflows/$workflow_file"
  echo
}

run_basic_checks() {
  activate_backend_venv
  (cd "$ROOT_DIR" && make test)
  (cd "$ROOT_DIR/workspaces/web/portal" && npm run build)
  (cd "$ROOT_DIR/workspaces/web/client" && npm run build)
}

run_quality_gate() {
  activate_backend_venv
  (cd "$ROOT_DIR/workspaces/backend" && python manage.py check)
  (cd "$ROOT_DIR/workspaces/backend" && make lint)
  (cd "$ROOT_DIR/workspaces/backend" && make test)
  (cd "$ROOT_DIR" && make test)
  (cd "$ROOT_DIR" && pytest)
  (cd "$ROOT_DIR/workspaces/web/portal" && npm run build)
  (cd "$ROOT_DIR/workspaces/web/client" && npm run build)
}

cmd="${1:-}"

case "$cmd" in
  start)
    show_workflow "W10_iniciar_sessao.md"
    echo "[session] Rodando checks basicos..."
    run_basic_checks
    ;;
  continue)
    show_workflow "W11_continuar_sessao.md"
    echo "[session] Rodando smoke rapido..."
    (cd "$ROOT_DIR" && bash scripts/smoke_stack_dev.sh)
    (cd "$ROOT_DIR" && bash scripts/smoke_client_dev.sh)
    ;;
  save)
    show_workflow "W12_salvar_checkpoint.md"
    echo "[session] Rodando quality gate minimo para checkpoint..."
    run_basic_checks
    ;;
  qa)
    show_workflow "W16_auditoria_qualidade.md"
    echo "[session] Rodando quality gate completo..."
    run_quality_gate
    ;;
  *)
    cat <<USAGE
Uso: ./scripts/session.sh <comando>

Comandos:
  start      Abre W10 e roda checks basicos
  continue   Abre W11 e roda smokes
  save       Abre W12 e roda quality gate minimo
  qa         Abre W16 e roda quality gate completo
USAGE
    exit 1
    ;;
esac
