---
id: W11
title: Continuar sessao
description: Retomar apos pausa com contexto e branch policy valida.
inputs:
  - agente (codex|antigravity)
  - objetivo_atual
  - modo_escrita (sim|nao)
outputs:
  - contexto_recarregado
  - plano_curto_de_execucao
commands:
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
  - bash scripts/gemini_check.sh
  - sed -n '1,220p' .agent/memory/CONTEXT_PACK.md
  - sed -n '1,220p' .agent/memory/TODO_NEXT.md
  - sed -n '1,220p' .agent/memory/IN_PROGRESS.md
  - git log -5 --oneline
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - bash scripts/smoke_stack_dev.sh
  - bash scripts/smoke_client_dev.sh
quality_gate:
  - smokes sem falha
memory_updates:
  - atualizar .agent/memory/IN_PROGRESS.md quando modo_escrita=sim
---

# W11 - Continuar sessao

## Branches canonicas
- Codex: `main` / `main/etapa-*`.
- Antigravity: `AntigravityIDE` / `AntigravityIDE/etapa-*`.
- Uniao: `Antigravity_Codex` apenas para integracao.

## Passos
1. Recarregar contexto (`GEMINI`, `CONTEXT_PACK`, `TODO_NEXT`, `IN_PROGRESS`).
2. Rodar `bash scripts/gemini_check.sh`.
3. Validar branch com `branch_guard`.
4. Rodar smoke rapido (`stack` e `client`).
5. Se `modo_escrita=sim`, registrar lock humano em `IN_PROGRESS.md`.

## Criterio de saida
- Objetivo unico definido e ambiente pronto para editar.
