# T6.3.2-A10 - Runtime do Cloudflare + monitoramento

Data: 27/02/2026
Status: concluida

## Objetivo
Completar a automacao da trilha Cloudflare adicionando controle de runtime do tunnel (`cloudflared`) e visibilidade operacional no monitoramento do ecossistema.

## Entregas

### Backend - Portal CMS
- Nova acao admin:
  - `POST /api/v1/portal/admin/config/cloudflare-runtime/`
- Acoes suportadas:
  - `start`
  - `stop`
  - `status`
- Runtime persiste:
  - PID em `.runtime/ops/pids/cloudflare.pid`
  - log em `.runtime/ops/logs/cloudflare.log`
- Retorno inclui ultimas linhas de log para exibicao no Web Admin.

### Backend - Monitoramento realtime
- `GET /api/v1/orders/ops/realtime/` passou a incluir o servico `cloudflare` em `services`.
- O servico cloudflare e monitorado por processo (sem porta local dedicada).

### Web Admin
- Secao `Portal CMS > Conectividade > Cloudflare online` ganhou:
  - botoes `Status runtime`, `Iniciar tunnel`, `Parar tunnel`
  - card de runtime com estado, PID, timestamps, comando e tail de log.

### Operacao (scripts)
- Novo script:
  - `scripts/cloudflare_tunnel.sh`
- Comandos:
  - `start`, `stop`, `restart`, `status`, `logs [linhas]`

## Validacao executada
- Backend: `ruff check` e `python manage.py check`.
- Web Admin: `npm run lint` e `npm run build`.
- Observacao: `pytest` backend permaneceu bloqueado nesta sessao por indisponibilidade do PostgreSQL local.

## Proximos passos
1. Integrar comando de runtime Cloudflare no `ops_center.py` como servico de primeira classe no TUI.
2. Adicionar hardening de timeout/retry para start/stop remoto do tunnel.
3. Reexecutar suite backend completa quando PostgreSQL estiver disponivel.
