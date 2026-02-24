---
id: W18
title: Preparar PR e merge
description: Preparar integracao sem conflito entre Codex e Antigravity.
inputs:
  - agente_executor (codex|antigravity)
  - branch_antigravity (opcional)
  - branch_destino (default: main)
outputs:
  - branch_pronta_para_pr
commands:
  - sed -n '1,220p' GEMINI.md
  - bash scripts/branch_guard.sh --agent <agente_executor> --strict --codex-primary feature/etapa-4-orders --allow-codex-join
  - git fetch origin
  - fluxo_codex: git checkout -B join/codex-ag feature/etapa-4-orders && git merge --no-ff <branch_antigravity>
  - fluxo_antigravity: manter ag/<tipo>/<slug> e abrir PR para integracao (sem merge em branch Codex)
  - executar W16_auditoria_qualidade
  - executar W21_sync_codex_antigravity
quality_gate:
  - branch_guard
  - auditoria completa + sync obrigatorio
memory_updates:
  - atualizar CHANGELOG se houver ajuste final pre-PR
---

# W18 - Preparar PR/Merge

## Regras por agente
- Codex:
  - integra em `join/codex-ag` e conduz merge final para PR.
- Antigravity:
  - permanece em `ag/<tipo>/<slug>`.
  - nunca commita/merge em `feature/etapa-4-orders` ou `join/codex-ag`.

## Passos
1. Ler `GEMINI.md`.
2. Validar branch com `branch_guard`.
3. Executar fluxo de integracao conforme agente.
4. Rodar `W16` + `W21`.
5. Publicar resumo de PR com arquivos alterados, validacoes e riscos.

## Criterio de saida
- Branch pronta para PR sem conflito entre agentes.
