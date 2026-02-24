---
id: W20
title: Limpar ambiente
description: Limpeza segura do ambiente de desenvolvimento sem afetar dados sensiveis ou producao.
inputs:
  - modo_limpeza (padrao|com_cache)
outputs:
  - ambiente_pronto_para_novo_start
commands:
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
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
1. Ler `/home/roberto/.gemini/GEMINI.md`.
2. Encerrar processos nas portas `8000`, `3000` e `3001`.
3. Remover locks stale de Next.
4. Validar ambiente pronto para novo start.
