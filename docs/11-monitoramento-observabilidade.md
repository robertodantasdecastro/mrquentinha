# Monitoramento, logs e observabilidade

## Objetivo
Ter visibilidade desde o MVP:
- saber quando o backend caiu
- medir erros
- rastrear operações críticas (pedido, compra, financeiro)

## Logs
- padrão: logs estruturados (JSON) quando for para produção
- no dev: logs legíveis no console
- registrar:
  - request_id (correlação)
  - usuário (id) quando autenticado
  - ação (ex.: “create_order”)

## Health checks
- `/api/v1/health` (simples)
- `/api/v1/ready` (opcional, checa DB)

## Erros
- MVP: logging + armazenamento de logs
- Fase 2: Sentry (ou similar) para rastrear exceptions

## Métricas
- latência por endpoint
- taxa de erro
- número de pedidos/dia
- custo médio por prato (derivado)

## Backups
- backup diário do Postgres
- retenção mínima (ex.: 7, 30, 90 dias conforme política)
