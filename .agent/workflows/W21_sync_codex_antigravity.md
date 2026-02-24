---
id: W21
title: Sync Codex <-> Antigravity
description: Workflow obrigatorio para sincronizar memoria/docs, validar qualidade e impedir divergencia entre Codex e Antigravity.
inputs:
  - escopo_da_mudanca
  - mensagem_commit (opcional)
outputs:
  - sync_concluido
  - commit_publicado
commands:
  - bash scripts/quality_gate_all.sh
  - bash scripts/sync_memory.sh --check
  - atualizar Sync Pack (PROJECT_STATE/CHANGELOG/DECISIONS/RUNBOOK/CONTEXT_PACK/TODO_NEXT)
  - validar segredos no diff (PASSWORD=|SECRET_KEY=|AKIA|-----BEGIN)
  - git commit + git push
quality_gate:
  - W16 executado (via quality_gate_all)
  - sync_memory em modo check sem pendencias
memory_updates:
  - Sync Pack revisado e atualizado conforme impacto
---

# W21 - Sync Codex <-> Antigravity

## Passos
1. Executar quality gate completo (equivalente ao W16):
   - `bash scripts/quality_gate_all.sh`
2. Atualizar Sync Pack:
   - `PROJECT_STATE`, `CHANGELOG`, `DECISIONS`, `RUNBOOK_DEV`, `CONTEXT_PACK`, `TODO_NEXT`.
3. Validar segredos no diff (working + staged):
   - padroes obrigatorios: `PASSWORD=`, `SECRET_KEY=`, `AKIA`, `-----BEGIN`.
4. Commitar com mensagem padronizada e fazer push.
5. Confirmar `git status` limpo.

## Criterio de saida
- Sincronizacao concluida, sem divergencia entre codigo, docs/memoria e workflows.
