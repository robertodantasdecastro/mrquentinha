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
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
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
1. Ler `/home/roberto/.gemini/GEMINI.md`.
2. Reproduzir bug com passos claros.
3. Criar teste que falha antes da correcao.
4. Implementar correcao minima e objetiva.
5. Rodar regressao no modulo e pontos impactados.
