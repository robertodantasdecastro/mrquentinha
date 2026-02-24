---
id: W10
title: Iniciar sessao
description: Comecar o trabalho com baseline tecnico validado, branch correta e contexto compartilhado.
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
  - sed -n '1,260p' docs/memory/PROJECT_STATE.md
  - sed -n '1,260p' docs/memory/DECISIONS.md
  - sed -n '1,220p' .agent/memory/IN_PROGRESS.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary feature/etapa-4-orders --allow-codex-join
  - cd workspaces/backend && source .venv/bin/activate && cd ~/mrquentinha && make test && pytest
  - source ~/.nvm/nvm.sh && nvm use --lts
  - cd workspaces/web/portal && npm run build
  - cd workspaces/web/client && npm run build
quality_gate:
  - baseline backend/frontend sem erro de build/test
memory_updates:
  - atualizar .agent/memory/IN_PROGRESS.md quando modo_escrita=sim
---

# W10 - Iniciar sessao

## Passos
1. Ler `AGENTS.md`, `GEMINI.md` e memoria oficial.
2. Ler `.agent/memory/IN_PROGRESS.md` para evitar colisao de edicao.
3. Validar branch do agente com `scripts/branch_guard.sh`.
4. Validar baseline:
   - backend com venv ativa (`make test` + `pytest` no root)
   - frontend com nvm LTS (`npm run build` portal/client)
5. Se `modo_escrita=sim`, atualizar `IN_PROGRESS.md` com:
   - agente, branch, etapa, arquivos/areas e proximo comando.

## Criterio de saida
- Emitir: `Sessao pronta` + checklist do dia.
