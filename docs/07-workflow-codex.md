# Workflow do Codex (estado atual)

## Base obrigatoria de contexto
Antes de qualquer tarefa, manter alinhado:
- `AGENTS.md`
- `docs/02-arquitetura.md`
- `docs/03-modelo-de-dados.md`
- `docs/memory/PROJECT_STATE.md`
- `docs/memory/DECISIONS.md`
- `docs/memory/CHANGELOG.md`
- `docs/memory/RUNBOOK_DEV.md`
- `.agent/memory/CONTEXT_PACK.md`

## Comandos padrao de desenvolvimento
No root (`~/mrquentinha`):

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Seed, smoke e sync:

```bash
./scripts/seed_demo.sh
./scripts/smoke_stack_dev.sh
./scripts/smoke_client_dev.sh
bash scripts/check_installer_workflow.sh --check
bash scripts/sync_memory.sh --check
bash scripts/quality_gate_all.sh
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

## Politica de Branches (Anti-Conflito)
- `BRANCH_CODEX_PRIMARY=feature/etapa-4-orders`
- Codex opera somente em `BRANCH_CODEX_PRIMARY`.
- Antigravity opera somente em `ag/<tipo>/<slug>`.
- Integracao entre agentes ocorre em `join/codex-ag`.
- Validacao obrigatoria antes de commit/push:

```bash
bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders
bash scripts/branch_guard.sh --agent antigravity --strict
bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders
```

## Regra Global de Sincronizacao
- Sempre rodar quality gate antes de commit final.
- Sempre rodar `bash scripts/sync_memory.sh --check` antes de commit.
- Sempre rodar `bash scripts/check_installer_workflow.sh --check` quando houver mudancas em trilhas de instalacao/deploy.
- Toda mudanca em backend/frontend/scripts deve refletir docs/memory e `.agent`.
- Nunca armazenar segredos em git (`.env` real, tokens, chaves, senhas).

## Compatibilidade de paths (Codex x Antigravity)
- Regra global lida pelo painel Antigravity: `.agent/rules/global.md`.
- Espelho para ordenacao no topo: `.agent/rules/00_GLOBAL_RULE.md`.
- Fontes completas mantidas em `.antigravity/GLOBAL_RULE.md` e `.antigravity/GLOBAL_SYNC_RULE.md`.

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
- `./scripts/smoke_client_dev.sh`

4. Sync e documentacao
- `bash scripts/sync_memory.sh --check`
- atualizar `docs/memory/CHANGELOG.md`
- atualizar `docs/memory/DECISIONS.md` quando houver decisao tecnica
- manter `docs/memory/PROJECT_STATE.md` e `docs/memory/RUNBOOK_DEV.md` coerentes com o estado real
