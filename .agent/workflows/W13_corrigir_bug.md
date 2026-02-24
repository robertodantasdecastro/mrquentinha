---
id: W13
title: Corrigir bug
description: Executar bugfix orientado por teste, com regressao e memoria atualizada.
inputs:
  - descricao_bug
  - modulo_afetado
outputs:
  - bug_corrigido
  - teste_regressao
commands:
  - reproduzir_cenario
  - criar_teste_falhando
  - implementar_correcao
  - rodar_testes_modulo
  - rodar_testes_regressao
quality_gate:
  - teste novo cobre bug e suite relevante passa
memory_updates:
  - CHANGELOG e DECISIONS quando houver regra nova
---

# W13 - Corrigir bug

## Passos
1. Reproduzir bug com passos claros.
2. Criar teste que falha antes da correcao.
3. Implementar correcao minima e objetiva.
4. Rodar regressao no modulo e pontos impactados.
5. Documentar causa raiz em `CHANGELOG` e, se necessario, `DECISIONS`.

## Criterio de saida
- Bug reproduzido, corrigido e coberto por teste.
