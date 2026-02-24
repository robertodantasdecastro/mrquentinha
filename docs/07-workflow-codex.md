# Workflow do Codex (estado atual)

## Base obrigatoria de contexto
Antes de qualquer tarefa, manter alinhado:
- `AGENTS.md`
- `docs/02-arquitetura.md`
- `docs/03-modelo-de-dados.md`
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/DECISIONS.md`
- `docs/memory/CHANGELOG.md`

## Comandos padrao de desenvolvimento
No root (`~/mrquentinha`):

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Seed e smoke:

```bash
./scripts/seed_demo.sh
./scripts/smoke_stack_dev.sh
./scripts/smoke_client_dev.sh
```

## Estrategia de prompts
Cada prompt deve conter:
1. objetivo claro
2. escopo (o que entra e o que nao entra)
3. Definition of Done
4. comandos exatos de validacao
5. arquivos/documentos de referencia

## Variaveis padrao (sem segredos)
- Backend:
  - `DATABASE_URL`
  - `DJANGO_SETTINGS_MODULE`
  - `DEBUG`
  - `SECRET_KEY`
  - `ALLOWED_HOSTS`
  - `CSRF_TRUSTED_ORIGINS`
  - `CORS_ALLOWED_ORIGINS`
- Portal:
  - `NEXT_PUBLIC_API_BASE_URL`
- Client:
  - `NEXT_PUBLIC_API_BASE_URL`
  - `NEXT_PUBLIC_DEMO_CUSTOMER_ID`

## Checklist antes de PR/merge
1. Backend
- `python manage.py check`
- `python manage.py makemigrations --check`
- `python manage.py migrate`
- `make lint`
- `make test`

2. Frontends
- `cd workspaces/web/portal && npm run lint && npm run build`
- `cd workspaces/web/client && npm run lint && npm run build`

3. Validacao funcional
- `./scripts/seed_demo.sh`
- `./scripts/smoke_stack_dev.sh`

4. Documentacao
- atualizar `docs/memory/CHANGELOG.md`
- atualizar `docs/memory/DECISIONS.md` quando houver decisao tecnica
- manter `docs/memory/PROJECT_STATE.md` e `docs/memory/RUNBOOK_DEV.md` coerentes com o estado real
