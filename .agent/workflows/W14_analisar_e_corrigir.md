---
id: W14
title: Analisar e corrigir
description: Investigacao profunda com coleta de evidencias, comparacao de solucoes e correcao definitiva.
inputs:
  - incidente
outputs:
  - causa_raiz
  - correcao_aplicada
  - troubleshooting_documentado
commands:
  - coletar_logs
  - formular_hipoteses
  - isolar_causa_raiz
  - propor_solucao_rapida
  - propor_solucao_correta
  - aplicar_solucao_correta
quality_gate:
  - validacao final + regressao direcionada
memory_updates:
  - atualizar RUNBOOK com troubleshooting do incidente
---

# W14 - Analisar e corrigir

## Passos
1. Coletar logs e sinais (API, frontend, scripts, banco).
2. Isolar causa raiz com experimento minimo reproduzivel.
3. Propor duas abordagens:
   - solucao rapida (mitigacao)
   - solucao correta (definitiva)
4. Aplicar a solucao correta.
5. Atualizar `docs/memory/RUNBOOK_DEV.md` com troubleshooting objetivo.

## Criterio de saida
- Causa raiz comprovada e correcao definitiva aplicada.
