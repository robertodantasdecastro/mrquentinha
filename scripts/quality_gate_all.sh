#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

activate_backend_venv() {
  local venv_activate="$ROOT_DIR/workspaces/backend/.venv/bin/activate"

  if [[ ! -f "$venv_activate" ]]; then
    echo "[quality_gate] ERRO: venv do backend nao encontrada em $venv_activate" >&2
    echo "[quality_gate] Crie/ative a venv antes de rodar o quality gate." >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$venv_activate"
}

ensure_nvm_lts() {
  if [[ ! -s "$HOME/.nvm/nvm.sh" ]]; then
    echo "[quality_gate] ERRO: nvm nao encontrado em ~/.nvm/nvm.sh" >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$HOME/.nvm/nvm.sh"

  if ! command -v nvm >/dev/null 2>&1; then
    echo "[quality_gate] ERRO: comando nvm indisponivel no shell atual." >&2
    exit 1
  fi

  nvm use --lts >/dev/null

  if ! command -v npm >/dev/null 2>&1; then
    echo "[quality_gate] ERRO: npm nao encontrado apos carregar nvm --lts." >&2
    exit 1
  fi
}

activate_backend_venv

echo "[quality_gate] Backend: python manage.py check"
(cd "$ROOT_DIR/workspaces/backend" && python manage.py check)

echo "[quality_gate] Backend: make lint"
(cd "$ROOT_DIR/workspaces/backend" && make lint)

echo "[quality_gate] Backend: make test"
(cd "$ROOT_DIR/workspaces/backend" && make test)

echo "[quality_gate] Root: make test"
(cd "$ROOT_DIR" && make test)

echo "[quality_gate] Root: pytest"
(cd "$ROOT_DIR" && pytest)

ensure_nvm_lts

echo "[quality_gate] Portal: npm run build"
(cd "$ROOT_DIR/workspaces/web/portal" && npm run build)

echo "[quality_gate] Client: npm run build"
(cd "$ROOT_DIR/workspaces/web/client" && npm run build)

if [[ -x "$ROOT_DIR/scripts/smoke_stack_dev.sh" ]]; then
  echo "[quality_gate] Smoke stack"
  (cd "$ROOT_DIR" && bash scripts/smoke_stack_dev.sh)
fi

if [[ -x "$ROOT_DIR/scripts/smoke_client_dev.sh" ]]; then
  echo "[quality_gate] Smoke client"
  (cd "$ROOT_DIR" && bash scripts/smoke_client_dev.sh)
fi

echo "[quality_gate] OK"
