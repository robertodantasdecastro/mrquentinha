# Relatorio de Evidencias Tecnicas (Auditoria)
Data: 02/03/2026

## Ambiente e escopo verificado
- Backend: `workspaces/backend`
- Frontends: `workspaces/web/admin`, `workspaces/web/client`, `workspaces/web/portal`, `workspaces/web/ui`
- Infra/scripts: `scripts/`, `installdev.sh`, `infra/nginx`

## Comandos executados
1. Busca de padroes sensiveis no repo (`rg` com chaves/tokens/secrets).
2. Revisao manual de settings Django (`base/dev/prod`), urls e endpoints publicos.
3. Revisao manual de scripts de deploy/producao (`setup_nginx_prod.sh`, `start_vm_prod.sh`, `installdev.sh`).
4. Revisao manual de fluxos de token no frontend (`storage.ts`).
5. `ruff check src tests` no backend.
6. `npm audit --omit=dev --audit-level=high` em cada frontend.
7. `DJANGO_SETTINGS_MODULE=config.settings.prod python manage.py check --deploy`.

## Resultados objetivos

### 1) Check de deploy Django
- Resultado: **3 warnings**
  - `security.W004` (HSTS nao definido)
  - `security.W008` (`SECURE_SSL_REDIRECT` nao habilitado)
  - `security.W009` (`SECRET_KEY` fraca)

### 2) Lint backend
- Resultado: **falhou** por estilo/import-order (nao por falha funcional critica).

### 3) Auditoria de dependencias frontend
- `web/admin`: `found 0 vulnerabilities`
- `web/client`: `found 0 vulnerabilities`
- `web/portal`: `found 0 vulnerabilities`

### 4) Dependencias Python de seguranca
- `pip_audit`: nao instalado no venv.
- `bandit`: nao instalado no venv.
- Consequencia: analise SCA/SAST Python parcial nesta rodada.

### 5) Estado de chave de aplicacao (sem exposicao do valor)
- Medicao local controlada: `SECRET_KEY` atual com tamanho abaixo do recomendado por `check --deploy`.

## Conclusao tecnica desta rodada
- A auditoria identificou riscos concretos e reproduziveis com evidencia em codigo.
- Nao houve alteracao de codigo da aplicacao nesta tarefa; somente consolidacao documental.

