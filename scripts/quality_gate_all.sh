#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ensure_npm() {
  if command -v npm >/dev/null 2>&1; then
    return
  fi

  if [[ -s "$HOME/.nvm/nvm.sh" ]]; then
    # shellcheck disable=SC1090
    source "$HOME/.nvm/nvm.sh"
    if command -v nvm >/dev/null 2>&1; then
      nvm use --silent default >/dev/null 2>&1 || nvm use --silent node >/dev/null 2>&1 || true
    fi
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "[quality_gate] ERRO: npm nao encontrado no PATH." >&2
    echo "[quality_gate] Instale Node.js/NPM ou configure NVM no ambiente atual." >&2
    exit 1
  fi
}

if [[ -f "$ROOT_DIR/workspaces/backend/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "$ROOT_DIR/workspaces/backend/.venv/bin/activate"
fi

echo "[quality_gate] Root: make test"
(cd "$ROOT_DIR" && make test)

echo "[quality_gate] Root: pytest"
(cd "$ROOT_DIR" && pytest)

echo "[quality_gate] Backend: make test"
(cd "$ROOT_DIR/workspaces/backend" && make test)

ensure_npm

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
