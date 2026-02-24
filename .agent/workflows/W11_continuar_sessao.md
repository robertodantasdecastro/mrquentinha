---
id: W11
title: Continuar sessao
description: Retomar sessao apos pausa com contexto tecnico, historico recente e smoke rapido.
inputs:
  - objetivo_atual
outputs:
  - contexto_recarregado
  - plano_curto_de_execucao
commands:
  - sed -n '1,260p' .agent/memory/CONTEXT_PACK.md
  - sed -n '1,220p' .agent/memory/TODO_NEXT.md
  - git log -5 --oneline
  - git branch --show-current
  - bash scripts/smoke_stack_dev.sh
  - bash scripts/smoke_client_dev.sh
quality_gate:
  - smoke scripts sem falhas
memory_updates:
  - atualizar TODO_NEXT se prioridade mudou
---

# W11 - Continuar sessao

## Passos
1. Ler `CONTEXT_PACK` e `TODO_NEXT`.
2. Revisar ultimos 5 commits com `git log -5 --oneline`.
3. Validar branch atual e objetivo da sessao.
4. Rodar smoke rapido:
   - `scripts/smoke_stack_dev.sh`
   - `scripts/smoke_client_dev.sh`
5. Reconfirmar proximo passo unico para execucao imediata.

## Criterio de saida
- Contexto restaurado e objetivo validado para continuar desenvolvimento.
