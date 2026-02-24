---
id: W17
title: Atualizar documentacao e memoria
description: Sincronizar docs/memory e .agent/memory com o estado real do projeto.
inputs:
  - mudancas_realizadas
outputs:
  - docs_sincronizadas
commands:
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
  - atualizar docs/memory/PROJECT_STATE.md
  - atualizar docs/memory/CHANGELOG.md
  - atualizar docs/memory/DECISIONS.md
  - atualizar docs/memory/RUNBOOK_DEV.md
  - atualizar .agent/memory/CONTEXT_PACK.md
  - atualizar .agent/memory/TODO_NEXT.md
  - bash scripts/sync_memory.sh --check
quality_gate:
  - docs sem segredos e com estado real validado
memory_updates:
  - aplicacao obrigatoria neste proprio workflow
---

# W17 - Atualizar documentacao/memoria

## Passos
1. Ler `/home/roberto/.gemini/GEMINI.md`.
2. Atualizar Sync Pack conforme impacto da entrega.
3. Validar sincronizacao com `bash scripts/sync_memory.sh --check`.
4. Conferir ausencia de segredos no diff.

## Criterio de saida
- Memoria coerente com codigo/scripts e pronta para checkpoint.
