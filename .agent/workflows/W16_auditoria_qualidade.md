---
id: W16
title: Auditoria de qualidade
description: Executar quality gate completo com venv e nvm padronizados.
inputs:
  - escopo_validacao (completo|parcial)
outputs:
  - relatorio_qa
commands:
  - sed -n '1,220p' GEMINI.md
  - cd workspaces/backend && source .venv/bin/activate && python manage.py check
  - cd workspaces/backend && source .venv/bin/activate && make lint
  - cd workspaces/backend && source .venv/bin/activate && make test
  - cd workspaces/backend && source .venv/bin/activate && cd ~/mrquentinha && make test && pytest
  - source ~/.nvm/nvm.sh && nvm use --lts
  - cd workspaces/web/portal && npm run lint && npm run build
  - cd workspaces/web/client && npm run lint && npm run build
  - bash scripts/smoke_stack_dev.sh
  - bash scripts/smoke_client_dev.sh
quality_gate:
  - todos os checks obrigatorios verdes
memory_updates:
  - registrar resultado resumido no CHANGELOG quando auditoria for marco de entrega
---

# W16 - Auditoria de qualidade

## Passos
1. Ler `GEMINI.md`.
2. Rodar backend com venv ativa (`check`, `lint`, `test`).
3. Rodar root (`make test`, `pytest`) com a mesma venv.
4. Carregar Node LTS (`nvm use --lts`) e rodar lint/build de portal e client.
5. Executar smokes (`stack` e `client`).
6. Emitir relatorio com status (OK/FALHA) e tempos.

## Criterio de saida
- Relatorio final com todos os itens executados e sem falha aberta.
