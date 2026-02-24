---
description: Bootstrap local do projeto para iniciar trabalho com stack completa e memoria carregada.
---

# Workflow 00 - Bootstrap

1. Ler `AGENTS.md` e memoria oficial (`PROJECT_STATE`, `DECISIONS`, `CHANGELOG`, `RUNBOOK_DEV`).
2. Verificar status do repo (`git status`) e registrar se ha alteracoes pendentes.
3. Conferir env minimo sem segredos em arquivos versionados (`.env.example`).
4. Subir backend, portal e client com os scripts oficiais.
5. Rodar `scripts/smoke_stack_dev.sh` e `scripts/smoke_client_dev.sh`.
6. Se smoke falhar, corrigir antes de iniciar qualquer feature.
