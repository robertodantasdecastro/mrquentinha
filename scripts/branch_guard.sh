#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<"USAGE"
Uso:
  bash scripts/branch_guard.sh --agent <codex|antigravity|union> [opcoes]

Opcoes:
  --agent <nome>                  Agente alvo: codex, antigravity ou union.
  --codex-primary <branch>        Branch principal do Codex (default: BRANCH_CODEX_PRIMARY ou main).
  --antigravity-branch <branch>   Branch principal do Antigravity (default: BRANCH_ANTIGRAVITY ou AntigravityIDE).
  --union-branch <branch>         Branch neutro de uniao (default: BRANCH_UNION ou Antigravity_Codex).
  --strict                        Retorna exit code 1 quando regra for violada.
  -h, --help                      Mostra ajuda.

Regras:
  Codex        -> main e main/etapa-*
  Antigravity  -> AntigravityIDE e AntigravityIDE/etapa-*
  Union        -> somente Antigravity_Codex (apenas merge/cherry-pick/PR)

Exemplos:
  bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
USAGE
}

AGENT=""
STRICT=0
CODEX_PRIMARY="${BRANCH_CODEX_PRIMARY:-main}"
ANTIGRAVITY_BRANCH="${BRANCH_ANTIGRAVITY:-AntigravityIDE}"
UNION_BRANCH="${BRANCH_UNION:-Antigravity_Codex}"

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
    --antigravity-branch)
      ANTIGRAVITY_BRANCH="${2:-}"
      shift 2
      ;;
    --union-branch)
      UNION_BRANCH="${2:-}"
      shift 2
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

violation=0

fail_msg() {
  echo "$1" >&2
  violation=1
}

case "$AGENT" in
  codex)
    if [[ "$CURRENT_BRANCH" != "$CODEX_PRIMARY" && "$CURRENT_BRANCH" != "$CODEX_PRIMARY"/etapa-* ]]; then
      fail_msg "[branch-guard] Violacao: Codex so pode operar em '$CODEX_PRIMARY' ou '$CODEX_PRIMARY/etapa-*'."
      echo "[branch-guard] Branch atual: '$CURRENT_BRANCH'" >&2
      echo "[branch-guard] Correcao (principal): git checkout '$CODEX_PRIMARY'" >&2
      echo "[branch-guard] Correcao (etapa): git checkout -b '$CODEX_PRIMARY/etapa-7.1-Auth-RBAC' '$CODEX_PRIMARY'" >&2
    fi

    if [[ "$CURRENT_BRANCH" == "$ANTIGRAVITY_BRANCH" || "$CURRENT_BRANCH" == "$ANTIGRAVITY_BRANCH"/etapa-* ]]; then
      fail_msg "[branch-guard] Violacao: Codex nao deve commitar em branch principal/etapa do Antigravity."
    fi
    ;;

  antigravity)
    if [[ "$CURRENT_BRANCH" != "$ANTIGRAVITY_BRANCH" && "$CURRENT_BRANCH" != "$ANTIGRAVITY_BRANCH"/etapa-* && "$CURRENT_BRANCH" != "$ANTIGRAVITY_BRANCH"-etapa-* ]]; then
      fail_msg "[branch-guard] Violacao: Antigravity so pode operar em '$ANTIGRAVITY_BRANCH' ou '$ANTIGRAVITY_BRANCH/etapa-*' (ou com hifen)."
      echo "[branch-guard] Branch atual: '$CURRENT_BRANCH'" >&2
      echo "[branch-guard] Correcao (principal): git checkout '$ANTIGRAVITY_BRANCH'" >&2
      echo "[branch-guard] Correcao (etapa): git checkout -b '$ANTIGRAVITY_BRANCH-etapa-7.1-Auth-RBAC' '$ANTIGRAVITY_BRANCH'" >&2
    fi

    if [[ "$CURRENT_BRANCH" == "$CODEX_PRIMARY" || "$CURRENT_BRANCH" == "$CODEX_PRIMARY"/etapa-* ]]; then
      fail_msg "[branch-guard] Violacao: Antigravity nao deve commitar em branch principal/etapa do Codex."
    fi
    ;;

  union)
    if [[ "$CURRENT_BRANCH" != "$UNION_BRANCH" ]]; then
      fail_msg "[branch-guard] Violacao: branch de uniao deve ser '$UNION_BRANCH'."
      echo "[branch-guard] Branch atual: '$CURRENT_BRANCH'" >&2
      echo "[branch-guard] Correcao: git checkout -B '$UNION_BRANCH' 'origin/$CODEX_PRIMARY'" >&2
    else
      if [[ -f .git/MERGE_HEAD || -f .git/CHERRY_PICK_HEAD ]]; then
        :
      elif ! git diff --quiet || ! git diff --cached --quiet; then
        fail_msg "[branch-guard] Violacao: '$UNION_BRANCH' nao e branch de trabalho diario. Use somente merge/cherry-pick/PR."
        echo "[branch-guard] Correcao: volte para '$CODEX_PRIMARY' ou '$ANTIGRAVITY_BRANCH' e mantenha desenvolvimento nas branches de etapa." >&2
      fi
    fi
    ;;

  *)
    echo "[branch-guard] Agent invalido: '$AGENT'. Use codex|antigravity|union." >&2
    exit 2
    ;;
esac

if [[ "$CURRENT_BRANCH" == "$UNION_BRANCH" && "$AGENT" != "union" ]]; then
  fail_msg "[branch-guard] Violacao: '$UNION_BRANCH' e branch neutro de integracao. Use --agent union para operar nela."
fi

if [[ $violation -eq 1 ]]; then
  if [[ $STRICT -eq 1 ]]; then
    exit 1
  fi
  exit 0
fi

echo "[branch-guard] OK: agente '$AGENT' em branch valida '$CURRENT_BRANCH'."
