#!/usr/bin/env bash
set -euo pipefail

GLOBAL_GEMINI="/home/roberto/.gemini/GEMINI.md"
SNAPSHOT="docs/memory/GEMINI_SNAPSHOT.md"

if [[ ! -f "$GLOBAL_GEMINI" ]]; then
  echo "[diff_gemini] ERRO: arquivo global nao encontrado: $GLOBAL_GEMINI" >&2
  exit 2
fi

if [[ ! -f "$SNAPSHOT" ]]; then
  echo "[diff_gemini] snapshot nao encontrado ($SNAPSHOT)." >&2
  echo "[diff_gemini] opcional: gere snapshot manual para documentacao." >&2
  exit 2
fi

if diff -u "$SNAPSHOT" "$GLOBAL_GEMINI"; then
  echo "[diff_gemini] Sem diferencas entre snapshot e global."
fi
