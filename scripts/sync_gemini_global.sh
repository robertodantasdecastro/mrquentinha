#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_GEMINI="$ROOT_DIR/GEMINI.md"
GLOBAL_GEMINI="$HOME/.gemini/GEMINI.md"
MODE="sync"

usage() {
  cat <<"USAGE"
Uso:
  bash scripts/sync_gemini_global.sh [--check]

Padrao:
  copia o GEMINI versionado do repo para ~/.gemini/GEMINI.md

Opcoes:
  --check   somente verifica divergencia (exit 1 se divergir)
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --check)
      MODE="check"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[sync_gemini] Opcao invalida: $arg" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ ! -f "$REPO_GEMINI" ]]; then
  echo "[sync_gemini] ERRO: arquivo nao encontrado: $REPO_GEMINI" >&2
  exit 1
fi

TMP_CANONICAL="$(mktemp)"
cleanup() {
  rm -f "$TMP_CANONICAL"
}
trap cleanup EXIT

awk '
  BEGIN { skip=0 }
  /^<!-- REPO_HEADER_START -->/ { skip=1; next }
  /^<!-- REPO_HEADER_END -->/ { skip=0; next }
  skip==0 { print }
' "$REPO_GEMINI" > "$TMP_CANONICAL"

validate_keys() {
  local target="$1"
  for key in BRANCH_CODEX_PRIMARY BRANCH_ANTIGRAVITY BRANCH_UNION; do
    if ! grep -q "$key" "$target"; then
      echo "[sync_gemini] ERRO: chave obrigatoria ausente em $target: $key" >&2
      exit 1
    fi
  done
}

validate_keys "$TMP_CANONICAL"

if [[ "$MODE" == "check" ]]; then
  if [[ ! -f "$GLOBAL_GEMINI" ]]; then
    echo "[sync_gemini] DIVERGENTE: arquivo global nao existe: $GLOBAL_GEMINI" >&2
    exit 1
  fi

  validate_keys "$GLOBAL_GEMINI"

  if diff -q "$TMP_CANONICAL" "$GLOBAL_GEMINI" >/dev/null; then
    echo "[sync_gemini] OK: repo e global estao sincronizados."
    exit 0
  fi

  echo "[sync_gemini] DIVERGENTE: repo e global estao diferentes." >&2
  echo "[sync_gemini] Execute: bash scripts/sync_gemini_global.sh" >&2
  exit 1
fi

mkdir -p "$(dirname "$GLOBAL_GEMINI")"
cp "$TMP_CANONICAL" "$GLOBAL_GEMINI"
validate_keys "$GLOBAL_GEMINI"

echo "[sync_gemini] OK: sincronizado para $GLOBAL_GEMINI"
