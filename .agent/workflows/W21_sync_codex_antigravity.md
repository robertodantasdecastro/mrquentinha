---
id: W21
title: Sync Codex <-> Antigravity
description: Workflow obrigatorio para sincronizar memoria/docs, validar qualidade e impedir divergencia entre agentes.
inputs:
  - agente (codex|antigravity|join)
  - mensagem_commit (opcional)
outputs:
  - sync_concluido
  - commit_publicado
commands:
  - sed -n '1,220p' GEMINI.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary feature/etapa-4-orders --allow-codex-join
  - bash scripts/quality_gate_all.sh
  - bash scripts/sync_memory.sh --check
  - atualizar Sync Pack (PROJECT_STATE/CHANGELOG/DECISIONS/RUNBOOK/CONTEXT_PACK/TODO_NEXT)
  - validar segredos no diff (PASSWORD=|SECRET_KEY=|AKIA|-----BEGIN)
  - git commit + git push (na branch do proprio agente)
quality_gate:
  - branch_guard em modo strict
  - W16 executado (via quality_gate_all)
  - sync_memory sem pendencias
memory_updates:
  - Sync Pack revisado e atualizado conforme impacto
---

# W21 - Sync Codex <-> Antigravity

## Regras por agente
- Codex: sincroniza/commita em `feature/etapa-4-orders` (ou `join/codex-ag` quando integracao).
- Antigravity: sincroniza/commita somente em `ag/<tipo>/<slug>`.
- Join: sincroniza apenas na branch `join/codex-ag`.

## Passos
1. Ler `GEMINI.md`.
2. Validar branch com `branch_guard`.
3. Rodar `quality_gate_all.sh`.
4. Rodar `sync_memory.sh --check`.
5. Validar segredos no diff e concluir commit/push na branch correta.

## Criterio de saida
- Codigo + docs/memoria sincronizados sem divergencia entre agentes.
