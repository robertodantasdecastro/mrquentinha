---
id: W10
title: Iniciar sessao
description: Comecar o trabalho com baseline validado, branch correta e lock humano.
inputs:
  - agente (codex|antigravity)
  - objetivo_dia
  - modo_escrita (sim|nao)
outputs:
  - sessao_pronta
  - checklist_dia
commands:
  - sed -n '1,220p' AGENTS.md
  - sed -n '1,220p' GEMINI.md
  - sed -n '1,220p' .agent/memory/IN_PROGRESS.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - cd workspaces/backend && source .venv/bin/activate && cd ~/mrquentinha && make test
  - source ~/.nvm/nvm.sh && nvm use --lts
  - cd workspaces/web/portal && npm run build
  - cd workspaces/web/client && npm run build
quality_gate:
  - baseline backend/frontend sem erro
memory_updates:
  - atualizar .agent/memory/IN_PROGRESS.md quando modo_escrita=sim
---

# W10 - Iniciar sessao

## Branches canonicas
- Codex: `main` e `main/etapa-*`.
- Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`.
- Uniao (nao diaria): `Antigravity_Codex`.

## Passos
1. Ler `AGENTS.md`, `GEMINI.md` e `IN_PROGRESS.md`.
2. Validar branch do agente com `branch_guard`.
3. Rodar baseline tecnico (backend + build portal/client).
4. Se `modo_escrita=sim`, atualizar `IN_PROGRESS.md` (agente, branch, etapa, areas tocadas).

## Criterio de saida
- Emitir `Sessao pronta` com checklist do dia.
