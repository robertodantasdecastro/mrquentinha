---
id: W12
title: Salvar checkpoint
description: Salvar progresso com branch policy valida, qualidade minima e memoria sincronizada.
inputs:
  - agente (codex|antigravity|union)
  - mensagem_checkpoint
outputs:
  - commit_checkpoint
commands:
  - sed -n '1,220p' GEMINI.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - git diff --stat
  - cd workspaces/backend && source .venv/bin/activate && make lint && make test
  - source ~/.nvm/nvm.sh && nvm use --lts
  - cd workspaces/web/portal && npm run build
  - cd workspaces/web/client && npm run build
  - git add ... && git commit -m "<mensagem>"
quality_gate:
  - branch_guard
  - backend lint/test + builds frontend
memory_updates:
  - atualizar docs/memory/CHANGELOG.md
---

# W12 - Salvar checkpoint

## Regras por agente
- Codex:
  - commit em `main` ou `main/etapa-*`.
- Antigravity:
  - commit em `AntigravityIDE` ou `AntigravityIDE/etapa-*`.
- Union:
  - commit apenas em `Antigravity_Codex` para merge/cherry-pick/integracao.
  - nao usar como branch de desenvolvimento diario.

## Passos
1. Ler `GEMINI.md`.
2. Validar branch com `branch_guard`.
3. Rodar quality gate minimo.
4. Atualizar `CHANGELOG`.
5. Commitar com mensagem rastreavel.
