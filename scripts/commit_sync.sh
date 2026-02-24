#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_MSG="chore: sync codex antigravity"

cd "$ROOT_DIR"

echo "[commit_sync] Rodando quality gate completo..."
bash scripts/quality_gate_all.sh

echo "[commit_sync] Rodando sync_memory em modo check..."
bash scripts/sync_memory.sh --check

COMMIT_MSG="${1:-}"
if [[ -z "$COMMIT_MSG" ]]; then
  if [[ -t 0 ]]; then
    read -r -p "Mensagem de commit [$DEFAULT_MSG]: " input_msg
    COMMIT_MSG="${input_msg:-$DEFAULT_MSG}"
  else
    COMMIT_MSG="$DEFAULT_MSG"
  fi
fi

git add \
  .antigravity/ \
  .agent/ \
  docs/memory/PROJECT_STATE.md \
  docs/memory/CHANGELOG.md \
  docs/memory/DECISIONS.md \
  docs/memory/RUNBOOK_DEV.md \
  docs/07-workflow-codex.md \
  scripts/sync_memory.sh \
  scripts/quality_gate_all.sh \
  scripts/commit_sync.sh

if git diff --cached --quiet; then
  echo "[commit_sync] Nenhuma alteracao staged para commit."
  exit 1
fi

git commit -m "$COMMIT_MSG"
git push

echo "[commit_sync] Finalizado com sucesso."
