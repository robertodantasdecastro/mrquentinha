# Arquitetura recomendada (sem Docker)

## Visão de componentes
- **Backend (API)**: Django + DRF
- **Web Gestão**: React (ou Next.js) consumindo a API
- **Mobile Cliente**: React Native (Expo ou Bare) consumindo a API
- **DB**: PostgreSQL
- **Armazenamento de mídia**: local no dev; S3 no deploy (fase posterior)
- **Proxy reverso**: Nginx (deploy)

## Princípios
- **Um backend global**: todos os clientes (mobile/web) acessam a mesma API.
- **Separação de responsabilidades**:
  - domínio e regras no backend
  - UI no web/mobile
- **Evolução por módulos**: cada domínio como um app Django.
- **Observabilidade desde cedo**: logs estruturados e métricas mínimas.

## Organização por domínios (Django apps)
- `accounts`: usuários, perfis, RBAC, OAuth
- `catalog`: pratos, cardápios, porções, preços
- `inventory`: estoque, unidades, movimentos, alertas
- `procurement`: requisições, compras, fornecedores
- `orders`: carrinho, pedidos, itens, status
- `finance`: contas, despesas, AP/AR, caixa, conciliação
- `ocr_ai`: captura/extração (fase 2)

## Integrações (via “ports/adapters”)
Crie interfaces estáveis (camada “ports”) para:
- gateways de pagamento (Pix/Cartão/VR)
- OCR (serviço externo ou interno)
- envio de e-mail/WhatsApp (futuro)

Isso permite trocar fornecedor sem refazer o domínio.

## Ambientes
- **Dev (offline)**: VM Linux, PostgreSQL local, serviços rodando via systemd opcional.
- **Prod (AWS)**: EC2 + Nginx + Gunicorn + PostgreSQL (RDS recomendado na fase 2/3).

## Recomendação de versionamento de API
- `/api/v1/...` no início
- manter compatibilidade ao evoluir (`v2` apenas quando necessário)

## Segurança (macro)
- OAuth Google para login
- JWT para chamadas mobile/web
- RBAC por permissões (DRF permissions)
- Rate limiting (fase 2)
