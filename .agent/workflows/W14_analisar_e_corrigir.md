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
  - sed -n '1,220p' GEMINI.md
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
1. Ler `GEMINI.md`.
2. Coletar logs e sinais.
3. Isolar causa raiz com experimento reproduzivel.
4. Aplicar solucao correta e atualizar troubleshooting.
