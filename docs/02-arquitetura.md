# Arquitetura recomendada (sem Docker)

## Visao de componentes
- **Backend (API)**: Django + DRF
- **Web Gestao**: React (ou Next.js) consumindo a API
- **Mobile Cliente**: React Native (Expo ou Bare) consumindo a API
- **DB**: PostgreSQL
- **Armazenamento de midia**: local no dev; S3 no deploy (fase posterior)
- **Proxy reverso**: Nginx (deploy)

## Principios
- **Um backend global**: todos os clientes (mobile/web) acessam a mesma API.
- **Separacao de responsabilidades**:
  - dominio e regras no backend
  - UI no web/mobile
- **Evolucao por modulos**: cada dominio como um app Django.
- **Service layer e selectors**:
  - `services.py` para regras de negocio e transacoes
  - `selectors.py` para consultas e leitura otimizada
- **Observabilidade desde cedo**: logs estruturados e metricas minimas.

## Organizacao por dominios (Django apps)
- `accounts`: usuarios, perfis, RBAC, OAuth
- `catalog`: pratos, cardapios, porcoes, precos
- `inventory`: estoque, unidades, movimentos, alertas
- `procurement`: requisicoes, compras, fornecedores
- `orders`: pedidos, itens, pagamentos e transicoes de status
- `finance`: contas, despesas, AP/AR, caixa, conciliacao
- `personal_finance`: contas/categorias/lancamentos pessoais por usuario (escopo privado), com recorrencia, resumo mensal e importacao CSV assistida
- `admin_audit`: auditoria de atividade administrativa (quem fez, quando, rota, status, latencia e metadata sanitizada)
- `ocr_ai`: captura/extracao (fase 2)

## Modulo Orders (Etapa 4)
Implementado no MVP com arquitetura orientada a regras no service layer.

Elementos principais:
- `orders/services.py`:
  - `create_order(...)` com validacao de `MenuDay` por `delivery_date`, validacao de pertencimento de `menu_item`, calculo de total e criacao de `Payment` `PENDING`.
  - `update_order_status(...)` com maquina de estados (`CREATED -> CONFIRMED -> IN_PROGRESS -> DELIVERED` e cancelamento antes de entregue).
- `orders/selectors.py`:
  - consultas de leitura para detalhes/listagem de pedidos/pagamentos.
- Endpoints DRF:
  - `/api/v1/orders/orders/`
  - `/api/v1/orders/orders/<id>/status/`
  - `/api/v1/orders/payments/`

## Nota de integracao com Finance (Etapa 5)
Para manter rastreabilidade entre evento operacional e evento financeiro:
- usar padrao `reference_type` + `reference_id` para vincular origem (`ORDER`, `PURCHASE`, etc.);
- aplicar idempotencia por referencia no financeiro (evitar duplicidade de AP/AR/Caixa quando o mesmo evento for processado novamente);
- manter criacao financeira desacoplada via service layer, sem logica financeira nas views de pedidos.

## Integracoes (via "ports/adapters")
Crie interfaces estaveis (camada "ports") para:
- gateways de pagamento (Pix/Cartao/VR)
- OCR (servico externo ou interno)
- envio de e-mail/WhatsApp (futuro)

Isso permite trocar fornecedor sem refazer o dominio.

### Estado atual de gateways (26/02/2026)
- Configuracao centralizada em `PortalConfig.payment_providers` (Admin Web) para:
  - providers habilitados (`mercadopago`, `efi`, `asaas`, `mock`);
  - ordem/fallback por metodo (`PIX`, `CARD`, `VR`);
  - dados de recebedor (`CPF/CNPJ`).
- Adaptadores implementados em `apps/orders/payment_providers.py`.
- Resolucao de provider por metodo em runtime em `apps/orders/provider_config.py`.
- Webhooks dedicados publicados por provider em `apps/orders/views.py`.

## Ambientes
- **Dev (offline)**: VM Linux, PostgreSQL local, servicos rodando via systemd opcional.
- **Prod (AWS)**: EC2 + Nginx + Gunicorn + PostgreSQL (RDS recomendado na fase 2/3).

## Recomendacao de versionamento de API
- `/api/v1/...` no inicio
- manter compatibilidade ao evoluir (`v2` apenas quando necessario)

## Seguranca (macro)
- OAuth Google para login
- JWT para chamadas mobile/web
- RBAC por permissoes (DRF permissions)
- Rate limiting (fase 2)
