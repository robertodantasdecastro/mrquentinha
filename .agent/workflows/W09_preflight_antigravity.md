---
id: W09
title: Preflight Antigravity
description: Preparar contexto usando GEMINI global unico antes de iniciar sessao.
inputs:
  - agente (codex|antigravity)
outputs:
  - preflight_ok
commands:
  - sed -n '1,220p' AGENTS.md
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
  - bash scripts/gemini_check.sh
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
quality_gate:
  - gemini_check sem erro
memory_updates:
  - nao obrigatorio
---

# W09 - Preflight Antigravity

## Objetivo
Garantir que o runtime do Antigravity usa a fonte global unica de regras antes de iniciar trabalho.

## Passos
1. Ler `AGENTS.md` e `/home/roberto/.gemini/GEMINI.md`.
2. Rodar `bash scripts/gemini_check.sh`.
3. Validar branch com `branch_guard`.

## Criterio de saida
- `preflight_ok` com GEMINI global valido e branch correta.
