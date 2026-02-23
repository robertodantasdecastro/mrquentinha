# Escopo do MVP (o que entra primeiro)

## Objetivo do MVP
Ter um sistema **operacional** para:
- publicar cardapio semanal
- receber pedidos
- registrar compras e atualizar estoque
- apurar custo e margem
- controlar financeiro basico (entradas/saidas, contas, fluxo de caixa)

## Limite do MVP operacional
O MVP operacional fecha na **Etapa 5 (Financeiro)**.

Status atual do desenvolvimento:
- **Etapas 0, 1, 2, 3, 3.1 e 4**: concluidas
- **Etapa 5**: planejada (subfases 5.0 a 5.5)

## Etapa 4 (concluida) - Pedidos no MVP
Entregas implementadas em pedidos:
- **Order**: cabecalho do pedido por data de entrega (`delivery_date`) e total.
- **OrderItem**: itens do pedido com `qty` e `unit_price` em snapshot.
- **Payment (MVP)**: registro inicial de pagamento com status `PENDING`.

Regras de negocio implementadas:
- validacao de `MenuDay` para a `delivery_date` informada;
- validacao de que cada `menu_item` pertence ao cardapio do mesmo dia;
- calculo de `total_amount` no service layer;
- maquina de status de pedido com transicoes controladas no service:
  - `CREATED -> CONFIRMED -> IN_PROGRESS -> DELIVERED`
  - `CANCELED` permitido ate antes de `DELIVERED`.

## Etapa 5 fecha o MVP operacional
A Etapa 5 integra o financeiro ao operacional com:
- AP (contas a pagar) a partir de compras
- AR (contas a receber) a partir de pedidos
- caixa e conciliacao de movimentos
- relatorio financeiro minimo (receitas x despesas)

## Funcionalidades do MVP (prioridade)
### A) Base de plataforma
- Autenticacao (Google OAuth) + JWT
- RBAC (perfis e permissoes)
- Auditoria minima (quem fez o que e quando)
- API REST versionada (`/api/v1`)

### B) Cardapio e produtos
- Cadastro de ingredientes
- Cadastro de pratos (receita: ingredientes + quantidades)
- Cardapio por data (semana)
- Parametros de porcao/marmita

### C) Estoque e compras
- Estoque por ingrediente (saldo, unidade)
- Movimentacoes (entrada por compra, saida por consumo/ajuste)
- Requisicao de compra quando estoque insuficiente
- Registro de compra manual (OCR entra na fase 2 como opcional)

### D) Pedidos e pagamentos (MVP enxuto)
- Cliente seleciona itens e data
- Status do pedido (criado, confirmado, em preparo, entregue/cancelado)
- Pagamento MVP com registro inicial `PENDING` e evolucao para gateway

### E) Financeiro (MVP ja com estrutura correta)
- Plano de contas simplificado
- Contas a pagar (AP) e a receber (AR)
- Despesas fixas/variaveis
- Fluxo de caixa diario/semanal
- Relatorio de resultado simplificado (receitas - despesas)

## Pos-MVP (planejado)
As **Etapas 6, 7 e 8** ficam fora do escopo do MVP operacional:
- **Etapa 6**: portal institucional (incluindo distribuicao via QR + links).
- **Etapa 7**: evolucao de canais web para clientes (ex.: PWA/web app).
- **Etapa 8**: consolidacao de governanca, seguranca e escalabilidade dos canais.

## Fora do MVP (planejado)
- OCR completo + validacao avancada
- VR/Cartao com conciliacao automatica
- Notificacoes push
- Multi-filial/lojas
- Modulo financeiro pessoal dos socios
