# ADR 0012 - Assistente de instalacao/deploy com workflow continuo

- Status: Aceita
- Data: 28/02/2026

## Contexto
O ecossistema evolui continuamente e o instalador pode ficar defasado quando mudam
scripts, backend de configuracao ou fluxo operacional do Web Admin.

Tambem havia necessidade de um fluxo guiado para operadores menos tecnicos
executarem instalacao/deploy com menor risco.

## Decisao
1. Criar no modulo `Administracao do servidor` um painel dedicado:
   - `Assistente de instalacao` com wizard por etapas.
2. Persistir estado do assistente no backend em `PortalConfig.installer_settings`.
3. Expor endpoints administrativos para:
   - validar payload do wizard;
   - salvar draft;
   - iniciar jobs;
   - consultar status;
   - cancelar;
   - listar jobs recentes.
4. Instituir guard rail operacional:
   - `scripts/check_installer_workflow.sh --check`
   integrado em `session`, `sync_memory` e `quality_gate_all`.

## Consequencias
- Beneficios:
  - instalacao/deploy com UX guiada e rastreavel;
  - menor drift entre capacidades reais da aplicacao e instalador;
  - memoria operacional atualizada como parte do fluxo obrigatorio.
- Trade-offs:
  - aumento de superficie de manutencao no app `portal`;
  - automacao SSH/cloud segue evolucao por fases, com base ja pronta para expandir.

## Implementacao
- Backend:
  - `workspaces/backend/src/apps/portal/models.py`
  - `workspaces/backend/src/apps/portal/services.py`
  - `workspaces/backend/src/apps/portal/views.py`
  - `workspaces/backend/src/apps/portal/migrations/0010_portalconfig_installer_settings.py`
- Web Admin:
  - `workspaces/web/admin/src/components/modules/InstallAssistantPanel.tsx`
  - `workspaces/web/admin/src/app/modulos/portal/sections.tsx`
  - `workspaces/web/admin/src/app/modulos/administracao-servidor/[service]/page.tsx`
- Operacao:
  - `scripts/check_installer_workflow.sh`
  - ajustes em `scripts/sync_memory.sh`, `scripts/quality_gate_all.sh` e `scripts/session.sh`

## Validacao
- `cd workspaces/backend && source .venv/bin/activate && python manage.py check`
- `cd workspaces/backend && source .venv/bin/activate && make lint`
- `cd workspaces/backend && source .venv/bin/activate && pytest tests/test_portal_api.py tests/test_portal_services.py`
- `cd workspaces/web/admin && npm run lint`
- `cd workspaces/web/admin && npm run build`
