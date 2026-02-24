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

## Regras
- Iniciar com golden tests passando.
- Fazer refatoracoes pequenas e isoladas.
- Rodar lint/test a cada passo relevante.
- Evitar mistura de refatoracao com mudanca funcional.

## Passos
1. Congelar baseline com testes existentes.
2. Refatorar em lotes pequenos.
3. Validar continuamente (`make lint`, `make test`, builds quando aplicavel).
4. Revisar diff para garantir ausencia de alteracao de comportamento.

## Criterio de saida
- Entrega PR-ready, sem regressao funcional.
