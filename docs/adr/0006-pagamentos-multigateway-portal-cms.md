# ADR-0006: Pagamentos multigateway com configuracao central no Portal CMS

## Status
Aceito

## Contexto
O MVP de pagamentos (`T7.2.1` a `T7.2.3`) estava funcional com provider `mock`, mas a operacao
precisa alternar entre provedores reais (Mercado Pago, Efi, Asaas), definir roteamento por metodo
(`PIX`, `CARD`, `VR`) e acompanhar status de transacao em tempo real sem rebuild dos frontends.

## Decisao
- Centralizar configuracao de pagamentos em `PortalConfig.payment_providers`.
- Permitir no Admin Web:
  - habilitar/desabilitar providers;
  - definir provider padrao e ordem por metodo;
  - configurar recebedor (`CPF`/`CNPJ`);
  - validar conectividade por provider com botao de teste.
- Evoluir backend de `orders` para:
  - resolver provider por metodo em runtime (`provider_config.py`);
  - suportar adaptadores de Mercado Pago, Efi e Asaas (`payment_providers.py`);
  - receber webhooks dedicados por provider e reaproveitar reconciliacao idempotente.
- Expor no payload publico somente configuracao segura (`configured`, `enabled`, roteamento),
  sem segredos.

## Consequencias
- Positivas:
  - troca de gateway sem deploy de client/mobile.
  - controle operacional centralizado no Admin Web.
  - continuidade do fluxo financeiro existente (`AR/Cash/Ledger`) com status em tempo real.
- Trade-offs:
  - aumento de complexidade operacional e de homologacao por provider.
  - necessidade de hardening adicional de assinatura/seguranca de webhook por fornecedor.

## Atualizacao 26/02/2026 (A2/A3)
- Evolucao aplicada:
  - configuracao ganhou `frontend_provider` com provider unico por canal (`web` e `mobile`).
  - backend passou a resolver provider por canal na criacao de intent (header `X-Client-Channel`), antes do fallback por metodo.
  - observabilidade publicada em `GET /api/v1/orders/ops/realtime/` com saude do ecossistema e comunicacao por provider.
- Impacto:
  - melhora de governanca operacional para cenarios em que web e mobile usam gateways diferentes.
  - capacidade de monitorar em tempo real falhas/sucesso de webhook e status de servicos no Admin.

## Alternativas consideradas
- Manter provider unico por ambiente via `.env`.
- Criar um microservico exclusivo para pagamentos nesta fase.
- Configurar credenciais de pagamento direto em cada frontend.
