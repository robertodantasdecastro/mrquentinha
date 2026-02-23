# Escopo do MVP (o que entra primeiro)

## Objetivo do MVP
Ter um sistema **operacional** para:
- publicar cardápio semanal
- receber pedidos
- registrar compras e atualizar estoque
- apurar custo e margem
- controlar financeiro básico (entradas/saídas, contas, fluxo de caixa)

## Funcionalidades do MVP (prioridade)
### A) Base de plataforma
- Autenticação (Google OAuth) + JWT
- RBAC (perfis e permissões)
- Auditoria mínima (quem fez o quê e quando)
- API REST versionada (`/api/v1`)

### B) Cardápio e produtos
- Cadastro de ingredientes
- Cadastro de pratos (receita: ingredientes + quantidades)
- Cardápio por data (semana)
- Parâmetros de porção/marmita

### C) Estoque e compras
- Estoque por ingrediente (saldo, unidade)
- Movimentações (entrada por compra, saída por consumo/ajuste)
- Requisição de compra quando estoque insuficiente
- Registro de compra manual (OCR entra na fase 2 como opcional)

### D) Pedidos e pagamentos (MVP enxuto)
- Cliente seleciona itens e data
- Status do pedido (criado, confirmado, em preparo, entregue/cancelado)
- Pagamento: iniciar com Pix (ex.: “confirmado manualmente” no MVP) e evoluir para gateway

### E) Financeiro (MVP já com estrutura correta)
- Plano de contas simplificado
- Contas a pagar (AP) e a receber (AR)
- Despesas fixas/variáveis
- Fluxo de caixa diário/semanal
- Relatório de resultado simplificado (receitas - despesas)

## Fora do MVP (planejado)
- OCR completo + validação avançada
- VR/Cartão com conciliação automática
- Notificações push
- Multi-filial/lojas
- Módulo financeiro pessoal dos sócios
