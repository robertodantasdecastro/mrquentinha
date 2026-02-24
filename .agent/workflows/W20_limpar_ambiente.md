---
id: W20
title: Limpar ambiente
description: Limpeza segura do ambiente de desenvolvimento sem afetar dados sensiveis ou producao.
inputs:
  - modo_limpeza (padrao|com_cache)
outputs:
  - ambiente_pronto_para_novo_start
commands:
  - encerrar processos portas 8000/3000/3001
  - remover locks .next/dev/lock
  - limpar caches opcionais
quality_gate:
  - nenhuma porta de dev ocupada apos limpeza
memory_updates:
  - sem alteracao obrigatoria
---

# W20 - Limpar ambiente

## Passos
1. Encerrar processos nas portas `8000`, `3000` e `3001`.
2. Remover locks stale:
   - `workspaces/web/portal/.next/dev/lock` (se existir)
   - `workspaces/web/client/.next/dev/lock` (se existir)
3. Limpar caches opcionais (somente desenvolvimento, sem dados de producao).
4. Validar ambiente livre para novo start.

## Criterio de saida
- Ambiente pronto para novo ciclo de execucao.
