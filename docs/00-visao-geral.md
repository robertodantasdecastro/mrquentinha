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

## Fluxo macro (do insumo ao pedido)
1. Gerente de Cozinha define o **cardapio da semana** (por data).
2. Cardapio referencia pratos e pratos referenciam ingredientes.
3. Sistema checa estoque: se faltar ingrediente, gera **requisicao de compra**.
4. Comprador registra compras:
   - opcional: foto de rotulo/contrarrotulo -> OCR -> pre-preenchimento
   - registra preco, unidade, quantidade, impostos, validade etc.
5. Sistema calcula:
   - custo por ingrediente
   - custo por prato
   - custo por marmita (porcao)
   - sugestao de preco de venda e margem
6. Cliente compra por mobile ou web clientes:
   - escolhe data/quantidade
   - paga (Pix/cartao/VR - MVP inicia com Pix e evolui)
7. Financeiro acompanha:
   - entradas (vendas)
   - saidas (compras + despesas gerais)
   - fluxo de caixa e DRE simplificada

## Fases sugeridas
- **MVP operacional (Etapas 0-5)**: base de plataforma, catalogo, estoque/compras, pedidos e financeiro.
- **Pos-MVP (Etapas 6-8)**: portal institucional, evolucao de canais web e governanca/escala.
