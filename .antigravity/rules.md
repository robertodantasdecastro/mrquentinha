# Regras Globais Antigravity - Mr Quentinha

## Leitura obrigatoria no inicio de cada tarefa
- `AGENTS.md`
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/DECISIONS.md`
- `docs/memory/CHANGELOG.md`
- `docs/memory/RUNBOOK_DEV.md`

## Seguranca e segredos
- Nunca comitar segredos (`.env` real, senhas, chaves, tokens).
- Manter no repositorio apenas arquivos de exemplo (`.env.example`) com placeholders.
- Nunca registrar valores sensiveis em docs, issues, commits ou logs versionados.

## Modo de trabalho obrigatorio
- Trabalhar em pequenos passos: implementar -> validar -> commit -> atualizar memoria.
- Sempre manter scripts de smoke funcionando (`scripts/smoke_stack_dev.sh` e `scripts/smoke_client_dev.sh`).
- Sempre atualizar `docs/memory/PROJECT_STATE.md` quando criar/alterar endpoints, scripts, portas ou fluxo operacional.

## Padrao de backend (Django/DRF)
- Seguir separacao por camadas: `services.py`, `selectors.py`, `serializers.py`, `views.py`, `urls.py`, `tests`.
- Evitar regra de negocio complexa em view/model.
- Priorizar testes de service + API para cada mudanca de comportamento.

## Padrao de frontend (Portal/Client)
- Reutilizar Design System compartilhado (`workspaces/web/ui`).
- Usar templates modulares e layout clean.
- Evitar hardcode de conteudo operacional; consumir dados da API sempre que aplicavel.

## Qualidade minima antes de concluir
- Backend: `python manage.py check`, `make lint`, `make test`.
- Frontends: `npm run lint` e `npm run build` em portal e client.
- Smokes: `scripts/smoke_stack_dev.sh` e `scripts/smoke_client_dev.sh`.
