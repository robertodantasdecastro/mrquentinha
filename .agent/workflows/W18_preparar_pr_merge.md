---
id: W18
title: Preparar PR e merge
description: Preparar branch para revisao e merge com quality gate e checklist DoD.
inputs:
  - branch_origem
  - branch_destino (default: main)
outputs:
  - branch_pronta_para_pr
commands:
  - git fetch origin
  - git rebase origin/main (ou merge main, se politica exigir)
  - executar W16_auditoria_qualidade
  - git log --oneline
  - validar ausencia de commits WIP
quality_gate:
  - auditoria completa + DoD atendido
memory_updates:
  - atualizar CHANGELOG se houve ajuste final pre-PR
---

# W18 - Preparar PR/Merge

## Passos
1. Sincronizar com `main` (rebase/merge conforme politica do time).
2. Executar auditoria de qualidade completa (W16).
3. Garantir historico limpo (sem commits `WIP`).
4. Validar checklist DoD do projeto.
5. Preparar resumo de PR:
   - objetivo
   - arquivos alterados
   - comandos de validacao
   - riscos conhecidos

## Criterio de saida
- Branch pronta para abrir PR e seguir para merge.
