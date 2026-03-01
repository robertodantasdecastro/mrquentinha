# ADR 0015 - Modulo dedicado de Auditoria de Atividade do Web Admin

Data: 01/03/2026  
Status: Aceita

## Contexto
A auditoria administrativa estava embutida no modulo `Administracao do servidor`.

Esse arranjo limitava:
- visibilidade executiva dos indicadores de auditoria;
- foco operacional para investigacao de eventos;
- separacao conceitual entre governanca de infraestrutura e governanca de trilha administrativa.

## Decisao
1. Remover a secao de auditoria do modulo `Administracao do servidor`.
2. Criar modulo proprio `Auditoria de atividade` no Web Admin (`/modulos/auditoria-atividade`).
3. Estruturar o modulo com paginas/ancoras dedicadas:
   - dashboard (KPI/indices);
   - eventos (filtros, paginação e detalhe);
   - seguranca (401/403/anonimos/falhas recentes);
   - tendencias (top atores, top rotas, grupos de acao, serie temporal).
4. Evoluir API de auditoria com endpoint de overview:
   - `GET /api/v1/admin-audit/admin-activity/overview/`
   - mantendo filtros equivalentes ao endpoint de listagem.
5. Tratar `Auditoria de atividade` como area tecnica (acesso restrito a admin no Web Admin).

## Consequencias
- Melhor segregacao de responsabilidades entre administracao de servidor e auditoria administrativa.
- Experiencia mais intuitiva para analise operacional e investigacao de incidentes.
- Indicadores de seguranca/latencia/erros acessiveis em modulo proprio para decisao rapida.
- Base pronta para evolucoes futuras: alertas, exportacao e trilha de compliance ampliada.

## Impacto tecnico
- Backend:
  - `apps/admin_audit/selectors.py`
  - `apps/admin_audit/views.py`
  - `apps/admin_audit/urls.py`
  - `config/urls.py`
- Web Admin:
  - `app/modulos/auditoria-atividade/*`
  - `components/AdminShell.tsx`
  - `lib/adminModules.ts`
  - `app/modulos/portal/sections.tsx` (remocao da secao antiga)
  - `app/modulos/administracao-servidor/[service]/page.tsx` (remocao de chave `auditoria`)
  - `lib/api.ts` e `types/api.ts` (overview da auditoria)
