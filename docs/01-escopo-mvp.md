# Escopo do MVP (o que entra primeiro)

## Objetivo do MVP
Ter um sistema **operacional** para:
- publicar cardapio semanal
- receber pedidos
- registrar compras e atualizar estoque
- apurar custo e margem
- controlar financeiro basico (entradas/saidas, contas, fluxo de caixa)

## Limite do MVP operacional
O MVP operacional e considerado fechado nas **Etapas 4 e 5**:
- **Etapa 4 (Pedidos)**: fluxo de pedido do cliente + status + pagamento MVP.
- **Etapa 5 (Financeiro)**: AP/AR, despesas, fluxo de caixa e relatorio financeiro minimo.

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
- Pagamento: iniciar com Pix (ex.: "confirmado manualmente" no MVP) e evoluir para gateway

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
