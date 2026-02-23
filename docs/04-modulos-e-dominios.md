# Módulos e domínios (para evoluir sem bagunça)

## Por que dividir por domínios
O projeto tem áreas bem diferentes (pedido, estoque, financeiro). Se você não separar,
vira um “monólito bagunçado” com dependências cruzadas.

A proposta aqui é um **monólito modular**:
- Um backend único (mais simples)
- Com módulos/domínios bem delimitados
- Preparado para virar microserviço no futuro (se precisar)

## Domínios e responsabilidades

### Accounts (Identidade e RBAC)
- usuários
- login Google
- gestão de perfis e permissões
- auditoria de acesso

### Catalog (Produtos e Cardápios)
- ingredientes (catálogo)
- pratos (receitas)
- cardápio por dia/semana
- preço de venda e disponibilidade

### Inventory (Estoque)
- saldo por ingrediente
- movimentações
- alertas e mínimo de estoque
- consumo por produção (fase 2)

### Procurement (Compras)
- requisição de compra
- compra e itens
- fornecedor
- entrada em estoque

### Orders (Vendas)
- pedidos e itens
- status
- integração de pagamento (fase 2 completo)

### Finance (Gestão financeira)
- plano de contas
- contas a pagar/receber
- despesas fixas/variáveis
- fluxo de caixa
- relatórios

### OCR_AI (Fase 2)
- ingestão de imagens
- extração por OCR
- validação e preenchimento assistido

## Regra de dependências (simples)
- `orders` pode ler `catalog`
- `procurement` pode escrever `inventory`
- `finance` referencia `orders` e `procurement` por `reference_type/reference_id`
- evitar import circular: usar serviços e interfaces
