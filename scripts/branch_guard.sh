#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Uso:
  bash scripts/branch_guard.sh --agent <codex|antigravity|join> [opcoes]

Opcoes:
  --agent <nome>             Agente alvo: codex, antigravity ou join.
  --codex-primary <branch>   Branch principal do Codex (default: $BRANCH_CODEX_PRIMARY).
  --join-branch <branch>     Branch de integracao (default: join/codex-ag).
  --allow-codex-join         Permite Codex operar na join branch (alem da branch principal).
  --strict                   Retorna exit code 1 quando regra for violada.
  -h, --help                 Mostra ajuda.

Exemplos:
  BRANCH_CODEX_PRIMARY=feature/etapa-4-orders \
    bash scripts/branch_guard.sh --agent codex --strict

  bash scripts/branch_guard.sh --agent codex --strict --allow-codex-join
  bash scripts/branch_guard.sh --agent antigravity --strict
  bash scripts/branch_guard.sh --agent join --strict
USAGE
}

AGENT=""
STRICT=0
ALLOW_CODEX_JOIN=0
CODEX_PRIMARY="${BRANCH_CODEX_PRIMARY:-}"
JOIN_BRANCH="join/codex-ag"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --agent)
      AGENT="${2:-}"
      shift 2
      ;;
    --codex-primary)
      CODEX_PRIMARY="${2:-}"
      shift 2
      ;;
    --join-branch)
      JOIN_BRANCH="${2:-}"
      shift 2
      ;;
    --allow-codex-join)
      ALLOW_CODEX_JOIN=1
      shift
      ;;
    --strict)
      STRICT=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[branch-guard] Opcao desconhecida: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$AGENT" ]]; then
  echo "[branch-guard] Informe --agent." >&2
  usage
  exit 2
fi

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
  echo "[branch-guard] Execute dentro de um repositorio git." >&2
  exit 2
fi

CURRENT_BRANCH="$(git branch --show-current)"
if [[ -z "$CURRENT_BRANCH" ]]; then
  echo "[branch-guard] HEAD destacada (detached). Troque para uma branch." >&2
  exit 2
fi

if [[ -z "$CODEX_PRIMARY" ]]; then
  CODEX_PRIMARY="$CURRENT_BRANCH"
fi

violation=0

case "$AGENT" in
  codex)
    codex_ok=0

    if [[ "$CURRENT_BRANCH" == "$CODEX_PRIMARY" ]]; then
      codex_ok=1
    fi

    if [[ $ALLOW_CODEX_JOIN -eq 1 && "$CURRENT_BRANCH" == "$JOIN_BRANCH" ]]; then
      codex_ok=1
    fi

    if [[ $codex_ok -ne 1 ]]; then
      echo "[branch-guard] Violacao: Codex deve operar em '$CODEX_PRIMARY'" >&2
      if [[ $ALLOW_CODEX_JOIN -eq 1 ]]; then
        echo "[branch-guard] (join permitida: '$JOIN_BRANCH')" >&2
      fi
      echo "[branch-guard] Branch atual: '$CURRENT_BRANCH'" >&2
      echo "[branch-guard] Correcao: git checkout '$CODEX_PRIMARY'" >&2
      if [[ $ALLOW_CODEX_JOIN -eq 1 ]]; then
        echo "[branch-guard] Ou para integracao: git checkout '$JOIN_BRANCH'" >&2
      fi
      violation=1
    fi
    ;;
  antigravity)
    if [[ ! "$CURRENT_BRANCH" =~ ^ag/[a-z0-9._-]+/[a-z0-9._-]+$ ]]; then
      echo "[branch-guard] Violacao: Antigravity deve usar branch no padrao ag/<tipo>/<slug>." >&2
      echo "[branch-guard] Branch atual: '$CURRENT_BRANCH'" >&2
      echo "[branch-guard] Exemplo: git checkout -b ag/chore/smoke-rbac" >&2
      violation=1
    fi
    ;;
  join)
    if [[ "$CURRENT_BRANCH" != "$JOIN_BRANCH" ]]; then
      echo "[branch-guard] Violacao: integracao Join deve ocorrer em '$JOIN_BRANCH'." >&2
      echo "[branch-guard] Branch atual: '$CURRENT_BRANCH'" >&2
      echo "[branch-guard] Correcao: git checkout -B '$JOIN_BRANCH' '$CODEX_PRIMARY'" >&2
      violation=1
    fi
    ;;
  *)
    echo "[branch-guard] Agent invalido: '$AGENT'. Use codex|antigravity|join." >&2
    exit 2
    ;;
esac

if [[ $violation -eq 1 ]]; then
  if [[ $STRICT -eq 1 ]]; then
    exit 1
  fi
  exit 0
fi

echo "[branch-guard] OK: agente '$AGENT' em branch valida '$CURRENT_BRANCH'."
