#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/workspaces/backend"
VENV_ACTIVATE="$BACKEND_DIR/.venv/bin/activate"

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[backend] Diretorio nao encontrado: $BACKEND_DIR" >&2
  exit 1
fi

if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "[backend] Virtualenv nao encontrado em $VENV_ACTIVATE" >&2
  echo "[backend] Crie com: cd workspaces/backend && python3 -m venv .venv" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$VENV_ACTIVATE"
cd "$BACKEND_DIR"

export PYTHONUNBUFFERED=1

echo "[backend] Aplicando migracoes..."
python manage.py migrate

echo "[backend] Iniciando servidor Django em http://0.0.0.0:8000"

child_pid=""

shutdown() {
  if [[ -n "$child_pid" ]] && kill -0 "$child_pid" 2>/dev/null; then
    kill "$child_pid" 2>/dev/null || true
    wait "$child_pid" 2>/dev/null || true
  fi
  echo "[backend] Encerrado."
  exit 0
}

trap shutdown INT TERM

python manage.py runserver 0.0.0.0:8000 &
child_pid=$!

set +e
wait "$child_pid"
status=$?
set -e

if [[ $status -eq 130 || $status -eq 143 ]]; then
  echo "[backend] Encerrado pelo usuario."
  exit 0
fi

exit "$status"
