# T6.3.2-A11 - Cloudflare DEV com dominios aleatorios

Data: 27/02/2026  
Status: concluida

## Objetivo
Permitir testes de desenvolvimento na internet sem depender do dominio oficial, usando URLs temporarias `trycloudflare.com` para Portal, Web Cliente, Web Admin e API.

## Entregas

### Backend (Portal CMS)
- `cloudflare_settings` evoluido com:
  - `dev_mode` (`bool`)
  - `dev_urls` (`portal/client/admin/api`)
- `POST /api/v1/portal/admin/config/cloudflare-runtime/`:
  - em `dev_mode=true`, inicia 4 tunnels (`--url`) e captura URLs por log.
  - sincroniza `dev_urls` no `PortalConfig`.
  - para os processos e limpa URLs temporarias no `stop`.
- `POST /api/v1/portal/admin/config/cloudflare-toggle/`:
  - `enabled=true` + `dev_mode=true`: habilita Cloudflare sem exigir dominio real.
  - `enabled=false`: encerra tunnel principal + tunnels dev e restaura modo local.
- `auto_apply_routes=true`:
  - atualiza automaticamente `api_base_url`, URLs dos frontends e `cors_allowed_origins` com base nas URLs dev.

### Web Admin
- Secao `Portal CMS > Conectividade > Cloudflare`:
  - novo toggle `Modo DEV com dominios aleatorios (trycloudflare)`;
  - campos de dominio/tunnel ficam desativados no modo DEV;
  - runtime exibe URLs geradas por servico (`portal/client/admin/api`).
- A tela e unica e compartilhada por todos os templates do admin.

### Testes
- Backend:
  - `test_cloudflare_preview_dev_mode_retorna_urls_trycloudflare`
  - `test_toggle_cloudflare_dev_mode_com_urls_aplica_enderecos`
- Validacoes executadas:
  - `python manage.py check`
  - `pytest tests/test_portal_services.py tests/test_portal_api.py`
  - `black --check src/apps/portal/services.py tests/test_portal_services.py`
  - `ruff check src/apps/portal/services.py tests/test_portal_services.py`
  - `npm run lint` (web/admin)
  - `npm run build` (web/admin)

## Resultado
O ambiente de desenvolvimento passa a operar com URLs publicas aleatorias sem bloqueio por DNS oficial, mantendo o fluxo de dominio real reservado ao modo operacional.
