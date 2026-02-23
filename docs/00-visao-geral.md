# Visao geral do produto

## O que e
Ecossistema digital completo da marca **Mr Quentinha**, com canais conectados:
- **Cliente (Mobile)**: ve cardapio por data, cria pedido, paga e acompanha status.
- **Gestao (Web)**: opera catalogo, estoque, compras, pedidos e financeiro.
- **Portal institucional (Web)**: apresenta a marca, servicos e canais oficiais.
- **Web clientes**: experiencia web para navegacao, compra e acompanhamento de pedidos.
- **Backend (API)**: centraliza regras de negocio, seguranca, persistencia e integracoes.

## Papel do portal (Etapa 6)
O portal institucional tambem funciona como:
- ponto de distribuicao digital (QR code + links para app e canais web);
- ponto de entrada para acesso rapido a gestao web;
- pagina oficial para comunicacao institucional da marca.

## Perfis de usuario (RBAC)
- **Cliente**: compra marmitas, acompanha pedidos, historico e pagamentos.
- **Admin**: configura tudo, gerencia usuarios internos, parametros e auditoria.
- **Gerente de Cozinha**: monta cardapios, define pratos e ingredientes, sinaliza necessidades.
- **Comprador**: recebe solicitacoes e registra compras (com suporte a OCR).
- **Financeiro**: contas a pagar/receber, fluxo de caixa, despesas fixas/variaveis, relatorios.

> Um mesmo usuario interno pode acumular perfis (ex.: Gerente de Cozinha + Comprador).

## Fluxo macro do MVP (cadeia de modulos)
**Catalog -> Inventory/Procurement -> Orders -> Finance (Etapa 5)**

1. **Catalog** publica o cardapio por data (`MenuDay` e `MenuItem`).
2. **Inventory/Procurement** valida disponibilidade de ingredientes e gera reposicao quando faltar insumo.
3. **Orders** cria pedidos por data do cardapio, com itens e snapshot de preco.
4. **Orders** cria `Payment` inicial com status `PENDING` no MVP.
5. **Finance (Etapa 5)** consome referencias do pedido/compra para gerar AR/AP e registrar caixa.

## Nota de integracao Orders -> Finance
Na Etapa 4, o pedido ja nasce com pagamento pendente e com base para integracao financeira por referencia.
Na Etapa 5, essa referencia sera usada para:
- **AR (contas a receber)** a partir de `Order`;
- **Caixa** a partir da liquidacao de pagamento;
- conciliacao entre evento operacional e evento financeiro.

## Fases sugeridas
- **MVP operacional (Etapas 0-5)**: base de plataforma, catalogo, estoque/compras, pedidos e financeiro.
- **Pos-MVP (Etapas 6-8)**: portal institucional, evolucao de canais web e governanca/escala.
