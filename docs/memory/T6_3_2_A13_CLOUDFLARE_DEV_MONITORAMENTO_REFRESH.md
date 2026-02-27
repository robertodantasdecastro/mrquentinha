# T6.3.2-A13 - Monitoramento DEV + refresh de dominios Cloudflare

Data: 27/02/2026  
Status: concluida

## Objetivo
Permitir que o Web Admin monitore estado e conectividade dos dominios aleatorios (`trycloudflare`) por servico e gere novos dominios com reconfiguracao automatica.

## Entregas

### Backend
- `manage_cloudflare_runtime` passou a aceitar `action=refresh`.
- Runtime DEV agora retorna por servico:
  - `connectivity` (`online`, `offline`, `unknown`)
  - `http_status`
  - `latency_ms`
  - `checked_url`
  - `checked_at`
  - `error`
- O `refresh` reinicia tunnels DEV, gera novos dominios aleatorios e reaplica rotas quando `auto_apply_routes` estiver ativo.

### Web Admin
- Painel Cloudflare ganhou botao:
  - `Gerar novos dominios DEV`
- Card de runtime ganhou monitoramento por servico com:
  - dominio atual
  - status de conectividade
  - HTTP/latencia
  - URL checada e timestamp
- Polling automatico de status em DEV ativo para manter monitoramento atualizado.

### Qualidade
- Testes backend atualizados:
  - `tests/test_portal_api.py` (acao `refresh`)
  - `tests/test_portal_services.py` (payload de conectividade no runtime DEV)
- Validacao executada:
  - `black`, `ruff`, `pytest` direcionado (`portal_api` e `portal_services`)
  - `npm run lint && npm run build` (web admin)

## Teste real no ambiente atual
- Tentativa de execucao real de `refresh` realizada.
- Resultado: bloqueado por ausencia do binario `cloudflared` no servidor de desenvolvimento.
- Mensagem observada: `Binario cloudflared nao encontrado no servidor.`
