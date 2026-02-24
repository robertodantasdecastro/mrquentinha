---
id: W18
title: Preparar PR e merge
description: Preparar branch para revisao e merge com quality gate e checklist DoD, incluindo branch de integracao join/codex-ag.
inputs:
  - branch_codex_primary (default: feature/etapa-4-orders)
  - branch_antigravity (opcional)
  - branch_destino (default: main)
outputs:
  - branch_pronta_para_pr
commands:
  - bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders
  - git fetch origin
  - git checkout -B join/codex-ag feature/etapa-4-orders
  - bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders
  - git merge --no-ff <branch_antigravity> (quando houver integracao)
  - executar W16_auditoria_qualidade
  - git log --oneline
  - validar ausencia de commits WIP
quality_gate:
  - branch_guard (codex/join)
  - auditoria completa + DoD atendido
memory_updates:
  - atualizar CHANGELOG se houve ajuste final pre-PR
---

# W18 - Preparar PR/Merge

## Passos
1. Partir da branch primaria do Codex:
   - `git checkout feature/etapa-4-orders`
   - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders`
2. Criar/atualizar branch de integracao:
   - `git checkout -B join/codex-ag feature/etapa-4-orders`
   - `bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders`
3. Integrar branch Antigravity (quando aplicavel):
   - `git merge --no-ff ag/<tipo>/<slug>`
4. Executar auditoria de qualidade completa (W16).
5. Garantir historico limpo (sem commits `WIP`).
6. Validar checklist DoD do projeto.
7. Preparar resumo de PR:
   - objetivo
   - arquivos alterados
   - comandos de validacao
   - riscos conhecidos

## Criterio de saida
- Integracao concluida em `join/codex-ag` e branch pronta para PR/merge.
