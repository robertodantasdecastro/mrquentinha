# T6.3.2-A12 - Automacao Cloudflare por terminal + sync de frontends

Data: 27/02/2026  
Status: concluida

## Objetivo
Permitir gerenciamento completo do Cloudflare (DEV e PRODUCAO) via terminal, mantendo paridade com o Web Admin e garantindo que os frontends consumam sempre a URL correta da API apos rotacao de endpoints.

## Entregas

### Scripts novos
- `scripts/cloudflare_admin_cli.py`
  - comandos:
    - `status`
    - `dev-up`, `dev-refresh`, `dev-down`
    - `preview-prod`, `prod-up`, `prod-refresh`, `prod-down`
    - `sync-frontends`
  - autenticacao:
    - `MQ_ADMIN_ACCESS_TOKEN`, ou
    - `MQ_ADMIN_USER` + `MQ_ADMIN_PASSWORD`
- `scripts/cloudflare_admin.sh`
  - wrapper bash para a CLI Python.
- `scripts/cloudflare_sync_frontends.sh`
  - atalho para sincronizar `.env.local` dos frontends com a URL atual da API.

### Scripts ajustados
- `scripts/start_admin_dev.sh`
- `scripts/start_client_dev.sh`

Ambos passaram a:
- priorizar `NEXT_PUBLIC_API_BASE_URL` de `.env.local`;
- usar fallback local apenas quando nao houver configuracao sincronizada.

## Resultado operacional
- Quando o runtime DEV gera novas URLs `trycloudflare`, o operador executa:
  - `./scripts/cloudflare_admin.sh dev-refresh`
- O comando atualiza runtime e sincroniza os frontends automaticamente.
- O mesmo fluxo existe para modo operacional por dominio oficial (`prod-up/prod-refresh`).

## Validacao executada
- `python3 -m py_compile scripts/cloudflare_admin_cli.py`
- `bash -n scripts/cloudflare_admin.sh scripts/cloudflare_sync_frontends.sh scripts/start_admin_dev.sh scripts/start_client_dev.sh`
- `scripts/cloudflare_admin.sh --help`
- `bash scripts/sync_memory.sh --check`
