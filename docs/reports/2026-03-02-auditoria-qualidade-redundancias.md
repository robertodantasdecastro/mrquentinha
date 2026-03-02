# Auditoria de Qualidade, Redundancias e Erros
Data: 02/03/2026

## Resumo
- Base funcional ampla, mas com pontos de acoplamento e duplicacao que aumentam custo de manutencao.
- Ha um erro estrutural relevante na forma de selecionar settings no backend CLI (efeito colateral em scripts).

## Falhas e inconsistencias objetivas

### QLT-001 - `manage.py` favorece `config.settings.dev` por default
- Evidencia: `workspaces/backend/manage.py:16`.
- Sintoma observado: comandos sem export explicito de `DJANGO_SETTINGS_MODULE` podem iniciar com settings erradas.
- Impacto:
  - comportamento nao deterministico entre scripts/sessoes;
  - risco de executar migrate/check em contexto incorreto.

### QLT-002 - `dev.py` adiciona `corsheaders` novamente
- Evidencia: `workspaces/backend/src/config/settings/dev.py:11`.
- Impacto:
  - potencial erro de labels duplicados e fragilidade de bootstrap.

### QLT-003 - Lint backend com pendencias
- Evidencias (`ruff check src tests`):
  - linhas longas em `accounts/serializers.py`, `accounts/services.py`, `portal/services.py`.
  - imports fora de ordem em:
    - `workspaces/backend/src/apps/portal/views.py`
    - `workspaces/backend/src/config/urls.py`
- Impacto:
  - ruido no CI e perda de consistencia.

## Redundancias (manutencao)

### RED-001 - Rotas runtime duplicadas em 3 frontends
- Arquivos duplicados por app:
  - `workspaces/web/admin/src/app/api/runtime/config/route.ts`
  - `workspaces/web/client/src/app/api/runtime/config/route.ts`
  - `workspaces/web/portal/src/app/api/runtime/config/route.ts`
  - `workspaces/web/admin/src/app/api/runtime/lookup-cep/route.ts`
  - `workspaces/web/client/src/app/api/runtime/lookup-cep/route.ts`
  - `workspaces/web/portal/src/app/api/runtime/lookup-cep/route.ts`
- Impacto:
  - risco de drift funcional e correcoes incompletas.

### RED-002 - `next.config.ts` muito similar entre admin/client/portal
- Arquivos:
  - `workspaces/web/admin/next.config.ts`
  - `workspaces/web/client/next.config.ts`
  - `workspaces/web/portal/next.config.ts`
- Impacto:
  - triplica manutencao de politicas de origem/imagens.

### RED-003 - Persistencia de tokens repetida entre frontends
- Arquivos:
  - `workspaces/web/admin/src/lib/storage.ts`
  - `workspaces/web/client/src/lib/storage.ts`
- Impacto:
  - comportamento de sessao pode divergir no tempo.

## Lacunas de engenharia (nao necessariamente bugs)
- Ausencia de baseline automatizada de seguranca Python (bandit/pip-audit indisponiveis no ambiente).
- Sem throttling central DRF para endpoints sensiveis/publicos.

## Testes e verificacoes executadas (somente leitura)
- `ruff check src tests` (backend) -> falhas de estilo/import-order.
- `npm audit --omit=dev --audit-level=high` em `web/admin`, `web/client`, `web/portal` -> sem vulnerabilidades high.
- `python manage.py check --deploy` com `DJANGO_SETTINGS_MODULE=config.settings.prod` -> warnings de seguranca (HSTS/SSL redirect/SECRET_KEY).

