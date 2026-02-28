#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="check"

INSTALLER_TRIGGER_REGEX='^(scripts/(install_mrquentinha\.sh|start_vm_prod\.sh|stop_vm_prod\.sh|docker_lifecycle\.sh|bootstrap_dev_vm\.sh)|workspaces/backend/src/apps/portal/|workspaces/backend/src/config/settings/|workspaces/web/admin/src/app/modulos/administracao-servidor/|workspaces/web/admin/src/app/modulos/portal/sections\.tsx|workspaces/web/admin/src/components/modules/InstallAssistantPanel\.tsx)'

INSTALLER_SYNC_PACK=(
  "scripts/install_mrquentinha.sh"
  "scripts/check_installer_workflow.sh"
  "workspaces/backend/src/apps/portal/models.py"
  "workspaces/backend/src/apps/portal/views.py"
  "workspaces/backend/src/apps/portal/services.py"
  "workspaces/web/admin/src/components/modules/InstallAssistantPanel.tsx"
  "docs/memory/PROJECT_STATE.md"
  "docs/memory/CHANGELOG.md"
  "docs/memory/DECISIONS.md"
  "docs/memory/RUNBOOK_DEV.md"
)

usage() {
  cat <<USAGE
Uso: bash scripts/check_installer_workflow.sh [--check]

Valida se mudancas em trilhas criticas de instalacao/deploy estao acompanhadas
de atualizacao do workflow do instalador e da memoria operacional.
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
      echo "[installer_workflow] Opcao invalida: $arg" >&2
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
  echo "[installer_workflow] Sem alteracoes em relacao ao HEAD."
  exit 0
fi

if ! echo "$changed_files" | grep -Eq "$INSTALLER_TRIGGER_REGEX"; then
  echo "[installer_workflow] Sem trigger critico de instalacao/deploy."
  exit 0
fi

sync_pack_changed=()
for f in "${INSTALLER_SYNC_PACK[@]}"; do
  if echo "$changed_files" | grep -Fxq "$f"; then
    sync_pack_changed+=("$f")
  fi
done

if [[ ${#sync_pack_changed[@]} -eq 0 ]]; then
  echo "[installer_workflow] ERRO: trigger critico detectado sem atualizacao do workflow do instalador." >&2
  echo "[installer_workflow] Atualize pelo menos um arquivo do Sync Pack do instalador:" >&2
  for f in "${INSTALLER_SYNC_PACK[@]}"; do
    echo "  - $f" >&2
  done
  exit 1
fi

echo "[installer_workflow] Trigger critico detectado com sync do instalador."
echo "[installer_workflow] Arquivos do sync pack alterados:"
for f in "${sync_pack_changed[@]}"; do
  echo "  - $f"
done

echo "[installer_workflow] OK ($MODE)."
