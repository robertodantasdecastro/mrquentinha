---
id: W10
title: Iniciar sessao
description: Comecar o trabalho do dia com baseline tecnico validado e contexto carregado.
inputs:
  - objetivo_dia (texto curto)
  - branch_esperada (opcional)
outputs:
  - sessao_pronta
  - checklist_dia
commands:
  - git status --short
  - sed -n '1,220p' AGENTS.md
  - sed -n '1,260p' docs/memory/PROJECT_STATE.md
  - sed -n '1,260p' docs/memory/DECISIONS.md
  - make test
  - (cd workspaces/web/portal && npm run build)
  - (cd workspaces/web/client && npm run build)
quality_gate:
  - baseline backend/frontend sem erro de build/test
memory_updates:
  - sem alteracao obrigatoria, exceto se estado real divergir da memoria
---

# W10 - Iniciar sessao

## Passos
1. Confirmar repo limpo com `git status --short`.
2. Ler contexto obrigatorio: `AGENTS.md`, `docs/memory/PROJECT_STATE.md`, `docs/memory/DECISIONS.md`.
3. Validar baseline minimo:
   - backend: `make test` (root ou backend)
   - portal: `npm run build`
   - client: `npm run build`
4. Verificar env minimo (apenas nomes, sem valores sensiveis):
   - `NEXT_PUBLIC_API_BASE_URL`
   - `DATABASE_URL`
   - `ALLOWED_HOSTS`
5. Definir checklist do dia (3 a 5 itens objetivos).

## Criterio de saida
- Emitir: `Sessao pronta`.
- Registrar checklist do dia com prioridade.
