---
id: W15
title: Refatoracao com limpeza
description: Refatorar codigo sem alterar comportamento externo, com seguranca por testes.
inputs:
  - alvo_refatoracao
outputs:
  - codigo_refatorado
  - comportamento_preservado
commands:
  - sed -n '1,220p' GEMINI.md
  - executar_golden_tests
  - refatorar_incrementalmente
  - rodar_lint_test_por_passo
  - revisar_diff
quality_gate:
  - golden tests + lint/test sem regressao
memory_updates:
  - registrar decisoes de refatoracao relevantes
---

# W15 - Refatoracao com limpeza

## Passos
1. Ler `GEMINI.md`.
2. Congelar baseline com golden tests.
3. Refatorar em lotes pequenos e validar continuamente.
4. Confirmar ausencia de mudanca comportamental.
