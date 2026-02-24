#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPO_GEMINI="$ROOT_DIR/GEMINI.md"
GLOBAL_GEMINI="$HOME/.gemini/GEMINI.md"
TMP_CANONICAL="$(mktemp)"
cleanup() {
  rm -f "$TMP_CANONICAL"
}
trap cleanup EXIT

if [[ ! -f "$REPO_GEMINI" ]]; then
  echo "[diff_gemini] ERRO: arquivo nao encontrado: $REPO_GEMINI" >&2
  exit 1
fi

if [[ ! -f "$GLOBAL_GEMINI" ]]; then
  echo "[diff_gemini] ERRO: arquivo global nao encontrado: $GLOBAL_GEMINI" >&2
  exit 1
fi

awk '
  BEGIN { skip=0 }
  /^<!-- REPO_HEADER_START -->/ { skip=1; next }
  /^<!-- REPO_HEADER_END -->/ { skip=0; next }
  skip==0 { print }
' "$REPO_GEMINI" > "$TMP_CANONICAL"

if diff -u "$TMP_CANONICAL" "$GLOBAL_GEMINI"; then
  echo "[diff_gemini] Sem diferencas."
fi
