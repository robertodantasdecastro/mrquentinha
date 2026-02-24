---
id: W11
title: Continuar sessao
description: Retomar apos pausa com contexto, lock humano e validacao rapida.
inputs:
  - agente (codex|antigravity)
  - objetivo_atual
  - modo_escrita (sim|nao)
outputs:
  - contexto_recarregado
  - plano_curto_de_execucao
commands:
  - sed -n '1,220p' GEMINI.md
  - sed -n '1,260p' .agent/memory/CONTEXT_PACK.md
  - sed -n '1,220p' .agent/memory/TODO_NEXT.md
  - sed -n '1,220p' .agent/memory/IN_PROGRESS.md
  - git log -5 --oneline
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary feature/etapa-4-orders --allow-codex-join
  - bash scripts/smoke_stack_dev.sh
  - bash scripts/smoke_client_dev.sh
quality_gate:
  - smoke scripts sem falhas
memory_updates:
  - atualizar .agent/memory/IN_PROGRESS.md quando modo_escrita=sim
---

# W11 - Continuar sessao

## Passos
1. Ler `GEMINI.md`, `CONTEXT_PACK`, `TODO_NEXT` e `IN_PROGRESS.md`.
2. Revisar ultimos commits e branch atual.
3. Validar branch com `branch_guard`.
4. Rodar smoke rapido (`stack` e `client`).
5. Se `modo_escrita=sim`, atualizar `IN_PROGRESS.md` antes de voltar a editar.

## Criterio de saida
- Contexto restaurado e objetivo unico definido para execucao.
