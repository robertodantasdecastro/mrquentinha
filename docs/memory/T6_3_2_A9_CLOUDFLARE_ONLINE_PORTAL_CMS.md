# T6.3.2-A9 - Cloudflare online no Portal CMS

Data: 27/02/2026
Status: concluida (implementacao tecnica)

## Objetivo
Permitir publicar todo o ecossistema (portal, web client, web admin e backend API) na internet via Cloudflare com UX de 1 clique no Web Admin, mantendo coexistencia com rede local.

## Entregas

### Backend
- `PortalConfig` ganhou `cloudflare_settings` (`JSONField`) para armazenar:
  - modo (`local_only`, `cloudflare_only`, `hybrid`),
  - dominio e subdominios por canal,
  - metadados de tunnel,
  - runtime e snapshot local para rollback.
- Servicos no `apps/portal/services.py`:
  - normalizacao de payload Cloudflare,
  - preview de rotas/URLs/CORS,
  - toggle ativar/desativar com atualizacao automatica dos endpoints.
- API admin no `apps/portal/views.py`:
  - `POST /api/v1/portal/admin/config/cloudflare-preview/`
  - `POST /api/v1/portal/admin/config/cloudflare-toggle/`
- Public config (`/api/v1/portal/config/`) passou a incluir bloco `cloudflare` sanitizado.

### Web Admin
- Modulo `Portal CMS > Conectividade` ganhou area `Cloudflare online (1 clique)` com:
  - selecao de modo de exposicao,
  - campos de dominio/subdominios,
  - metadados de tunnel,
  - preview de rotas e comando sugerido,
  - botoes `Pre-visualizar rotas`, `Ativar Cloudflare` e `Desativar Cloudflare`.

### Testes
- Novos testes:
  - `tests/test_portal_services.py` (preview e toggle).
  - `tests/test_portal_api.py` (actions cloudflare preview/toggle).

## Validacao executada
- Backend lint: `ruff check ...` (OK).
- Backend check: `python manage.py check` (OK).
- Web Admin: `npm run lint` e `npm run build` (OK).
- Observacao: `pytest` backend nao executou nesta sessao por indisponibilidade de conexao com PostgreSQL local.

## Resultado funcional
- E possivel manter local e Cloudflare sem conflito usando `mode=hybrid`.
- Ao desativar Cloudflare, o sistema restaura o snapshot local automaticamente.

## Proximos passos
1. Homologar credenciais reais Cloudflare (zone/tunnel/token) por ambiente.
2. Integrar runbook/script operacional para subir/parar processo `cloudflared` com observabilidade no painel de monitoramento.
3. Executar bateria completa de testes backend apos restaurar conectividade do PostgreSQL.
