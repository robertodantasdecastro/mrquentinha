#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"
VENV_ACTIVATE="$BACKEND_DIR/.venv/bin/activate"

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[seed-demo] Diretorio do backend nao encontrado: $BACKEND_DIR" >&2
  exit 1
fi

if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "[seed-demo] Virtualenv nao encontrada em: $VENV_ACTIVATE" >&2
  echo "[seed-demo] Crie com: cd workspaces/backend && python3 -m venv .venv" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$VENV_ACTIVATE"
cd "$BACKEND_DIR"

python manage.py migrate
python manage.py seed_demo

echo "[seed-demo] Dados DEMO aplicados com sucesso."
