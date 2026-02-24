#!/usr/bin/env bash
set -euo pipefail

GEMINI_GLOBAL="/home/roberto/.gemini/GEMINI.md"

usage() {
  cat <<'USAGE'
Uso:
  bash scripts/gemini_check.sh

Valida a fonte unica de regras globais:
  /home/roberto/.gemini/GEMINI.md

Saida:
  0  arquivo valido
  2  arquivo ausente ou chave obrigatoria ausente
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -f "$GEMINI_GLOBAL" ]]; then
  echo "[gemini_check] ERRO: fonte global nao encontrada: $GEMINI_GLOBAL" >&2
  echo "[gemini_check] Corrija criando/ajustando o arquivo global no Antigravity: ~/.gemini/GEMINI.md" >&2
  exit 2
fi

missing=0
for key in BRANCH_CODEX_PRIMARY BRANCH_ANTIGRAVITY BRANCH_UNION; do
  if ! grep -Eq "$key.*=" "$GEMINI_GLOBAL"; then
    echo "[gemini_check] ERRO: chave obrigatoria ausente em $GEMINI_GLOBAL: $key" >&2
    missing=1
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo "[gemini_check] Corrija as linhas no formato: BRANCH_...=valor (aceita bullets/backticks na mesma linha)." >&2
  exit 2
fi

echo "[gemini_check] OK: /home/roberto/.gemini/GEMINI.md valido."
