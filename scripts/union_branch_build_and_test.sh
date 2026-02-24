#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DRY_RUN=0
REMOTE="origin"
CODEX_PRIMARY="${BRANCH_CODEX_PRIMARY:-main}"
ANTIGRAVITY_BRANCH="${BRANCH_ANTIGRAVITY:-AntigravityIDE}"
UNION_BRANCH="${BRANCH_UNION:-Antigravity_Codex}"

usage() {
  cat <<"USAGE"
Uso:
  bash scripts/union_branch_build_and_test.sh [--dry-run] [--remote <origin>]

Fluxo:
  1) Atualiza main
  2) Cria/reseta Antigravity_Codex a partir de origin/main
  3) Merge de origin/AntigravityIDE
  4) Roda validacoes backend/root/frontend/smokes
  5) Push de Antigravity_Codex
USAGE
}

run() {
  local cmd="$1"
  echo "+ $cmd"
  if [[ $DRY_RUN -eq 1 ]]; then
    return 0
  fi
  bash -lc "$cmd"
}

ensure_clean() {
  if [[ $DRY_RUN -eq 1 ]]; then
    return 0
  fi

  if ! (cd "$ROOT_DIR" && git diff --quiet && git diff --cached --quiet); then
    echo "[union] ERRO: working tree sujo. Commit/stash antes de executar." >&2
    exit 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --remote)
      REMOTE="${2:-origin}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[union] Opcao invalida: $1" >&2
      usage
      exit 2
      ;;
  esac
done

trap 'if [[ -f "$ROOT_DIR/.git/MERGE_HEAD" ]]; then echo "[union] Conflito detectado no merge. Resolva manualmente e reexecute." >&2; fi' ERR

ensure_clean

run "cd '$ROOT_DIR' && git checkout '$CODEX_PRIMARY' && git pull --ff-only '$REMOTE' '$CODEX_PRIMARY'"
run "cd '$ROOT_DIR' && git fetch '$REMOTE'"
run "cd '$ROOT_DIR' && git checkout -B '$UNION_BRANCH' '$REMOTE/$CODEX_PRIMARY'"
run "cd '$ROOT_DIR' && git merge --no-ff '$REMOTE/$ANTIGRAVITY_BRANCH' -m 'merge: $ANTIGRAVITY_BRANCH -> $UNION_BRANCH'"

run "cd '$ROOT_DIR/workspaces/backend' && source .venv/bin/activate && python manage.py check"
run "cd '$ROOT_DIR/workspaces/backend' && source .venv/bin/activate && python manage.py makemigrations --check"
run "cd '$ROOT_DIR/workspaces/backend' && source .venv/bin/activate && make lint"
run "cd '$ROOT_DIR/workspaces/backend' && source .venv/bin/activate && make test"

run "cd '$ROOT_DIR' && make test"

run "source ~/.nvm/nvm.sh && nvm use --lts >/dev/null && cd '$ROOT_DIR/workspaces/web/portal' && npm run build"
run "source ~/.nvm/nvm.sh && nvm use --lts >/dev/null && cd '$ROOT_DIR/workspaces/web/client' && npm run build"

run "cd '$ROOT_DIR' && ./scripts/smoke_stack_dev.sh"
run "cd '$ROOT_DIR' && ./scripts/smoke_client_dev.sh"

run "cd '$ROOT_DIR' && bash scripts/branch_guard.sh --agent union --strict --codex-primary '$CODEX_PRIMARY' --antigravity-branch '$ANTIGRAVITY_BRANCH' --union-branch '$UNION_BRANCH'"
run "cd '$ROOT_DIR' && git push -u '$REMOTE' '$UNION_BRANCH'"

echo "[union] OK: uniao validada e publicada em '$UNION_BRANCH'."
