---
id: W09
title: Preflight Antigravity
description: Preparar contexto e sincronizar GEMINI runtime antes de iniciar sessao.
inputs:
  - agente (codex|antigravity)
outputs:
  - preflight_ok
commands:
  - sed -n '1,220p' AGENTS.md
  - sed -n '1,220p' GEMINI.md
  - bash scripts/sync_gemini_global.sh --check || bash scripts/sync_gemini_global.sh
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
quality_gate:
  - GEMINI repo/global sincronizado
memory_updates:
  - nao obrigatorio
---

# W09 - Preflight Antigravity

## Objetivo
Garantir que o runtime do Antigravity esta alinhado com o GEMINI versionado antes de iniciar trabalho.

## Passos
1. Ler `AGENTS.md` e `GEMINI.md`.
2. Verificar sincronismo com `sync_gemini_global.sh --check`.
3. Se divergir, executar `sync_gemini_global.sh`.
4. Validar branch com `branch_guard`.

## Criterio de saida
- `preflight_ok` com GEMINI sincronizado e branch valida.
