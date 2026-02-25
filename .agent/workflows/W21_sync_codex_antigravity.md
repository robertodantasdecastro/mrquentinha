---
id: W21
title: Sync Codex <-> Antigravity
description: Sincronizar memoria/docs com branch policy valida, quality gate e GEMINI global valido.
inputs:
  - agente (codex|antigravity|union)
outputs:
  - sync_concluido
commands:
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
  - bash scripts/gemini_check.sh
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - bash scripts/quality_gate_all.sh
  - bash scripts/sync_memory.sh --check
  - atualizar Sync Pack (PROJECT_STATE/CHANGELOG/DECISIONS/RUNBOOK/CONTEXT_PACK/TODO_NEXT)
quality_gate:
  - gemini_check sem erro
  - branch_guard em modo strict
  - quality_gate_all sem erro
  - sync_memory sem pendencias
memory_updates:
  - Sync Pack atualizado conforme impacto
---

# W21 - Sync Codex <-> Antigravity

## Branches sugeridas por agente
- Codex: `main` (ou `main-etapa-*` durante desenvolvimento por etapa).
- Antigravity: `AntigravityIDE` (ou `AntigravityIDE/etapa-*`).
- Union: `Antigravity_Codex` (somente integracao por merge/cherry-pick/PR).

## Passos
1. Ler `/home/roberto/.gemini/GEMINI.md`.
2. Rodar `gemini_check.sh`.
3. Validar branch com `branch_guard` no agente correto.
4. Rodar `quality_gate_all.sh`.
5. Rodar `sync_memory.sh --check`.
6. Validar segredos no diff e concluir commit/push na branch permitida.

## Criterio de saida
- Codigo + memoria sincronizados sem divergencia entre agentes.
