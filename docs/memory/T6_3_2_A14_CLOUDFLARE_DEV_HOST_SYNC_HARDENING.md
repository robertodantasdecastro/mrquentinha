# T6.3.2-A14 - Hardening de rotacao DEV (host + sync)

Data: 27/02/2026  
Status: concluida

## Objetivo
Garantir que, ao rotacionar dominios aleatorios do Cloudflare DEV, o backend e os frontends passem a usar automaticamente o dominio vigente sem drift.

## Entregas

### Backend
- `manage_cloudflare_runtime(action=\"status\")` agora:
  - detecta mudanca de `dev_urls` observada no runtime;
  - atualiza `cloudflare_settings.dev_urls`;
  - reaplica rotas no `PortalConfig` (`api_base_url`, `portal/client/admin_base_url`) quando `auto_apply_routes` estiver ativo.
- `config.settings.dev` passou a incluir `*.trycloudflare.com` em `ALLOWED_HOSTS`.

### Operacao
- script `scripts/install_cloudflared_local.sh` criado para instalar `cloudflared` em `.runtime/bin` (sem apt/sudo).

## Validacao executada
- `black`, `ruff` e `pytest` direcionado (`tests/test_portal_services.py`, `tests/test_portal_api.py`) em `OK`.
- teste real:
  - `refresh` gerou dominios `trycloudflare`;
  - monitoramento por servico estabilizou em `online` para `portal/client/admin/api`;
  - checagem de match confirmou sincronizacao do payload publico com `dev_urls` detectadas em runtime.
