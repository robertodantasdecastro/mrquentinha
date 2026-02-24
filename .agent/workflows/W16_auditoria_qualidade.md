---
id: W16
title: Auditoria de qualidade
description: Executar quality gate completo e produzir relatorio com status e tempos por etapa.
inputs:
  - escopo_validacao (completo|parcial)
outputs:
  - relatorio_qa
commands:
  - (cd workspaces/backend && source .venv/bin/activate && python manage.py check)
  - (cd workspaces/backend && source .venv/bin/activate && make lint)
  - (cd workspaces/backend && source .venv/bin/activate && make test)
  - make test
  - pytest
  - (cd workspaces/web/portal && npm run lint && npm run build)
  - (cd workspaces/web/client && npm run lint && npm run build)
  - bash scripts/smoke_stack_dev.sh
  - bash scripts/smoke_client_dev.sh
quality_gate:
  - todos os checks obrigatorios verdes
memory_updates:
  - registrar resultado resumido no CHANGELOG quando auditoria for marco de entrega
---

# W16 - Auditoria de qualidade

## Passos
1. Rodar backend completo:
   - `python manage.py check`
   - `make lint`
   - `make test`
2. Rodar root:
   - `make test`
   - `pytest`
3. Rodar frontend:
   - portal: `npm run lint` + `npm run build`
   - client: `npm run lint` + `npm run build`
4. Rodar smokes:
   - `scripts/smoke_stack_dev.sh`
   - `scripts/smoke_client_dev.sh`
5. Emitir relatorio com status (OK/FALHA) e tempo por etapa.

## Criterio de saida
- Relatorio final com todos os itens e tempos executados.
