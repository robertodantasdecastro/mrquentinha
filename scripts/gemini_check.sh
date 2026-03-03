#!/usr/bin/env bash
set -euo pipefail

DEFAULT_GEMINI_GLOBAL="$HOME/.gemini/GEMINI.md"
LINUX_GEMINI_GLOBAL="/home/roberto/.gemini/GEMINI.md"
MAC_GEMINI_GLOBAL="/Users/roberto/.gemini/GEMINI.md"
GEMINI_GLOBAL=""

usage() {
  cat <<'USAGE'
Uso:
  bash scripts/gemini_check.sh

Valida a fonte unica de regras globais:
  ~/.gemini/GEMINI.md (com fallback Linux/macOS)

Saida:
  0  arquivo valido
  2  arquivo ausente ou chave obrigatoria ausente
USAGE
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ -f "$DEFAULT_GEMINI_GLOBAL" ]]; then
  GEMINI_GLOBAL="$DEFAULT_GEMINI_GLOBAL"
elif [[ -f "$LINUX_GEMINI_GLOBAL" ]]; then
  GEMINI_GLOBAL="$LINUX_GEMINI_GLOBAL"
elif [[ -f "$MAC_GEMINI_GLOBAL" ]]; then
  GEMINI_GLOBAL="$MAC_GEMINI_GLOBAL"
else
  GEMINI_GLOBAL="$DEFAULT_GEMINI_GLOBAL"
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

echo "[gemini_check] OK: $GEMINI_GLOBAL valido."
