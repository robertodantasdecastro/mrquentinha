#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="check"
RUN_QUICK_GATE="false"

SYNC_PACK=(
  "docs/memory/PROJECT_STATE.md"
  "docs/memory/CHANGELOG.md"
  "docs/memory/DECISIONS.md"
  "docs/memory/RUNBOOK_DEV.md"
  ".agent/memory/CONTEXT_PACK.md"
  ".agent/memory/TODO_NEXT.md"
  "docs/07-workflow-codex.md"
  ".agent/workflows/USAGE_GUIDE.md"
)

activate_backend_venv() {
  local venv_activate="$ROOT_DIR/workspaces/backend/.venv/bin/activate"

  if [[ ! -f "$venv_activate" ]]; then
    echo "[sync_memory] ERRO: venv nao encontrada em $venv_activate" >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$venv_activate"
}

ensure_nvm_lts() {
  if [[ ! -s "$HOME/.nvm/nvm.sh" ]]; then
    echo "[sync_memory] ERRO: nvm nao encontrado em ~/.nvm/nvm.sh" >&2
    exit 1
  fi

  # shellcheck disable=SC1090
  source "$HOME/.nvm/nvm.sh"

  if ! command -v nvm >/dev/null 2>&1; then
    echo "[sync_memory] ERRO: comando nvm indisponivel." >&2
    exit 1
  fi

  nvm use --lts >/dev/null

  if ! command -v npm >/dev/null 2>&1; then
    echo "[sync_memory] ERRO: npm nao encontrado apos nvm --lts." >&2
    exit 1
  fi
}

usage() {
  cat <<USAGE
Uso: bash scripts/sync_memory.sh [--check] [--quick-gate]

Opcoes:
  --check       Executa checagem de sincronizacao (padrao)
  --quick-gate  Roda gate rapido: make test + pytest + build portal/client
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --check)
      MODE="check"
      ;;
    --quick-gate)
      RUN_QUICK_GATE="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[sync_memory] Opcao invalida: $arg" >&2
      usage
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

tracked_changes="$(git diff --name-only HEAD)"
untracked_changes="$(git ls-files --others --exclude-standard)"
changed_files="$(printf "%s\n%s\n" "$tracked_changes" "$untracked_changes" | awk 'NF' | sort -u)"

if [[ -z "$changed_files" ]]; then
  echo "[sync_memory] Sem alteracoes em relacao ao HEAD."
  exit 0
fi

trigger_changed="false"
if echo "$changed_files" | grep -Eq '^(workspaces/backend/|workspaces/web/|scripts/)'; then
  trigger_changed="true"
fi

sync_pack_changed=()
for f in "${SYNC_PACK[@]}"; do
  if echo "$changed_files" | grep -Fxq "$f"; then
    sync_pack_changed+=("$f")
  fi
done

if [[ "$trigger_changed" == "true" ]] && [[ ${#sync_pack_changed[@]} -eq 0 ]]; then
  echo "[sync_memory] AVISO: mudancas detectadas em backend/web/scripts sem atualizacao do Sync Pack." >&2
  echo "[sync_memory] Atualize pelo menos um arquivo do Sync Pack relevante:" >&2
  for f in "${SYNC_PACK[@]}"; do
    echo "  - $f" >&2
  done
  exit 1
fi

if [[ "$trigger_changed" == "true" ]]; then
  echo "[sync_memory] Trigger de sincronizacao detectado."
  if [[ ${#sync_pack_changed[@]} -gt 0 ]]; then
    echo "[sync_memory] Arquivos do Sync Pack alterados:"
    for f in "${sync_pack_changed[@]}"; do
      echo "  - $f"
    done
  fi
else
  echo "[sync_memory] Sem trigger em backend/web/scripts."
fi

if [[ "$RUN_QUICK_GATE" == "true" ]]; then
  echo "[sync_memory] Rodando quick gate..."

  activate_backend_venv
  (cd "$ROOT_DIR" && make test)
  (cd "$ROOT_DIR" && pytest)

  ensure_nvm_lts
  (cd "$ROOT_DIR/workspaces/web/portal" && npm run build)
  (cd "$ROOT_DIR/workspaces/web/client" && npm run build)
fi

echo "[sync_memory] OK ($MODE)."
