# ADR 0008 - Exposicao online via Cloudflare no Portal CMS

- Status: Aceita
- Data: 27/02/2026

## Contexto
A operacao precisava publicar Portal, Web Cliente, Web Admin e Backend API na internet com menor friccao operacional, mantendo a arquitetura atual da VM/local sem troca para containers.
Tambem era necessario permitir ativacao/desativacao rapida e previsivel pelo Web Admin.

## Decisao
1. `PortalConfig` passa a persistir `cloudflare_settings` (JSON) com:
   - modo de exposicao (`local_only`, `cloudflare_only`, `hybrid`),
   - dominio raiz e subdominios por canal (`portal/client/admin/api`),
   - metadados de tunnel (name/id/token) e runtime,
   - snapshot de conectividade local para rollback automatizado.
2. Foram adicionados endpoints admin no modulo Portal CMS:
   - `POST /api/v1/portal/admin/config/cloudflare-preview/`
   - `POST /api/v1/portal/admin/config/cloudflare-toggle/`
3. O toggle aplica automaticamente URLs base (`portal/client/admin/api/backend`) e CORS conforme modo escolhido.
4. O modo `hybrid` foi definido como estrategia padrao para coexistencia sem conflito entre rede local e Cloudflare.
5. No modo de desenvolvimento, `dev_mode=true` habilita tunelamento via URLs aleatorias `trycloudflare.com` por servico (`portal/client/admin/api`), sem exigir dominio real.

## Consequencias
- Beneficios:
  - Publicacao online com UX de 1 clique no Web Admin.
  - Rollback para modo local com restauracao automatica de snapshot.
  - Menor risco operacional na homologacao de webhooks de pagamento externos.
  - Desenvolvimento e QA externo desacoplados de DNS oficial, com endpoints temporarios gerados automaticamente.
- Trade-offs:
  - Execucao real do processo `cloudflared` continua responsabilidade operacional (runbook/script), nao do backend HTTP.
  - Segredos ficam centralizados no backend e nao sao expostos no payload publico.
  - URLs `trycloudflare` sao efemeras e mudam a cada restart; nao devem ser usadas como endpoint fixo de operacao.

## Implementacao
- Backend:
  - `PortalConfig.cloudflare_settings`.
  - normalizacao, preview e toggle em `apps/portal/services.py`.
  - runtime dev com 4 processos `cloudflared tunnel --url ...` e sincronizacao de `dev_urls`.
  - actions admin em `apps/portal/views.py`.
- Web Admin:
  - nova area `Cloudflare online (1 clique)` no modulo `Portal CMS > Conectividade`.
  - preview de rotas/urls e botoes de ativar/desativar.
  - toggle `Modo DEV com dominios aleatorios (trycloudflare)` e exibicao de URLs por servico no card de runtime.
- Operacao terminal:
  - script `scripts/cloudflare_admin.sh` para executar status/toggle/runtime/preview via API admin.
  - script `scripts/cloudflare_sync_frontends.sh` para sincronizar `.env.local` dos frontends com a URL atual da API.
- Testes:
  - cobertura adicionada em `tests/test_portal_api.py` e `tests/test_portal_services.py`.
  - cenarios DEV cobertos para preview e aplicacao automatica de URLs `trycloudflare`.
