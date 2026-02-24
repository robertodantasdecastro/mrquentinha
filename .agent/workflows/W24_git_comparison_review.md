---
id: W24
title: Revisao Comparativa de Branches
description: Comparar main vs AntigravityIDE vs Antigravity_Codex e gerar relatorio de diferencas.
inputs:
  - agente (codex|antigravity|union)
  - branches (default: main, AntigravityIDE, Antigravity_Codex)
outputs:
  - docs/memory/GIT_COMPARE_REPORT.md
commands:
  - ler GEMINI.md e AGENTS.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - git fetch origin
  - git log --left-right --graph e git diff --stat entre branches alvo
  - consolidar riscos/conflitos/pontos de integracao
  - atualizar docs/memory/GIT_COMPARE_REPORT.md
quality_gate:
  - relatorio objetivo com proximos passos acionaveis
memory_updates:
  - docs/memory/GIT_COMPARE_REPORT.md
---

# W24 - Revisao Comparativa de Branches

## Entrega
Gerar `docs/memory/GIT_COMPARE_REPORT.md` com:
1. diferencas por branch;
2. conflitos potenciais;
3. recomendacao de ordem de integracao.
