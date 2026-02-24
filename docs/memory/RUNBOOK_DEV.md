# Runbook DEV (stack completo)

## 1) Subir stack local
No root (`~/mrquentinha`), em terminais separados:

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Acessos:
- API: `http://127.0.0.1:8000`
- Portal: `http://127.0.0.1:3000`
- Web Cliente: `http://127.0.0.1:3001`

## 2) Sessao e paralelo (Codex + Antigravity)
1. Ler `AGENTS.md` e `GEMINI.md`.
2. Ler `.agent/memory/IN_PROGRESS.md`.
3. Validar branch:

```bash
bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
```

4. Atualizar lock humano (`IN_PROGRESS.md`) antes de editar.

## 3) Smoke
Validacao ponta a ponta:

```bash
./scripts/smoke_stack_dev.sh
```

Validacao rapida do client:

```bash
./scripts/smoke_client_dev.sh
```

### 3.1) Smoke apos hardening RBAC
- Endpoint privado `/api/v1/catalog/menus/` nao e usado no smoke.
- Endpoint publico read-only usado para smoke/frontends:
  - `GET /api/v1/catalog/menus/today/`
- CRUD do catalogo permanece protegido por RBAC.

## 4) Seed DEMO
Com backend pronto:

```bash
./scripts/seed_demo.sh
```

## 5) Quality gate padronizado
```bash
bash scripts/quality_gate_all.sh
```

O script garante:
- venv backend ativa
- Node via `nvm use --lts`
- checks backend/root/frontends/smokes

## 6) Sync obrigatorio antes de commit final
```bash
bash scripts/sync_memory.sh --check
```

## 7) Uniao oficial (main + AntigravityIDE)
```bash
./scripts/union_branch_build_and_test.sh
```

Simulacao sem executar:
```bash
./scripts/union_branch_build_and_test.sh --dry-run
```

## 8) Troubleshooting
- `DisallowedHost`:
  - revisar `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- CORS:
  - revisar `CORS_ALLOWED_ORIGINS`.
- Next lock:
  - remover apenas `workspaces/web/client/.next/dev/lock` apos encerrar processo.
- Porta ocupada:
  - `ss -ltnp | grep -E ':8000|:3000|:3001'`

## 9) Qualidade manual (fallback)
Backend:

```bash
cd workspaces/backend
source .venv/bin/activate
python manage.py check
python manage.py makemigrations --check
make lint
make test
```

Root:

```bash
cd ~/mrquentinha
source workspaces/backend/.venv/bin/activate
make test
pytest
```

Frontends:

```bash
source ~/.nvm/nvm.sh && nvm use --lts
cd workspaces/web/portal && npm run build
cd workspaces/web/client && npm run build
```
