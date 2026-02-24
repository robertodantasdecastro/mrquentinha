# Visao geral do produto

## O que e
Ecossistema digital da marca **Mr Quentinha**, com canais conectados por uma API unica:
- **Backend (Django + DRF)**: regra de negocio, persistencia, integracoes e auditoria.
- **Portal institucional (web)**: comunicacao da marca, cardapio publico e distribuicao digital.
- **Web Cliente (PWA-like)**: consulta de cardapio, carrinho, criacao de pedidos e historico.
- **Web Gestao (planejado)**: operacao interna completa (catalogo, compras, estoque, financeiro).
- **Mobile Cliente (planejado)**: experiencia nativa para pedidos e acompanhamento.

## Papel do portal (Etapa 6)
O portal institucional tambem funciona como:
- ponto oficial de distribuicao (QR Code + links de download/acesso);
- entrada para area de gestao (`admin`/backoffice);
- vitrine institucional e canal de contato.

## Fluxo macro do sistema (estado atual)
**Catalog -> Inventory/Procurement -> Production -> Orders -> Finance**

1. `Catalog` define ingredientes, pratos e cardapio por data.
2. `Inventory/Procurement` abastece estoque por compras e requisicoes.
3. `Production` consome estoque por lote com base nas receitas.
4. `Orders` recebe pedidos por data do cardapio e controla status/pagamento.
5. `Finance` consolida AP/AR, caixa, ledger, conciliacao, fechamento e relatorios.
6. `OCR` apoia captura de dados de rotulos/comprovantes para acelerar cadastro/operacao.

## Estado de entrega por fases
- **Concluidas**: 0, 1, 2, 3, 3.1, 4, 5.0, 5.1, 5.2, 5.3, 5.4, 5.5, 5.6.1, 5.6.2, 5.6.3, 6.0, 6.0.1, 7.0.
- **Em seguida (prioridade)**:
  - 7.1: autenticacao + RBAC completo
  - 7.2: pagamentos online/gateway
  - 6.1: nginx local/reverse proxy consolidado
  - 8: trilha de financas pessoais e expansao do ecossistema

## Perfis (RBAC alvo)
- **Cliente**: consulta cardapio, cria/acompanha pedidos.
- **Cozinha**: cardapio, producao e necessidades de compra.
- **Compras/Estoque**: compras, estoque e conciliacao operacional.
- **Financeiro**: AP/AR/caixa/relatorios e fechamento.
- **Admin**: governanca geral, configuracoes e auditoria.
