# Visão geral do produto

## O que é
Sistema completo para operação de marmitas — **Mr Quentinha**:
- **Cliente (Mobile)**: vê cardápio por data (semana), cria pedido, paga e acompanha status.
- **Gestão (Web)**: gerencia cardápios, estoque, compras, custos, vendas e **gestão financeira**.
- **Backend (API)**: centraliza regras, segurança, persistência e integrações (pagamentos/OCR/etc.).

## Perfis de usuário (RBAC)
- **Cliente**: compra marmitas, acompanha pedidos, histórico e pagamentos.
- **Admin**: configura tudo, gerencia usuários internos, parâmetros e auditoria.
- **Gerente de Cozinha**: monta cardápios, define pratos e ingredientes, sinaliza necessidades.
- **Comprador**: recebe solicitações e registra compras (com suporte a OCR).
- **Financeiro**: contas a pagar/receber, fluxo de caixa, despesas fixas/variáveis, relatórios.

> Um mesmo usuário interno pode acumular perfis (ex.: Gerente de Cozinha + Comprador).

## Fluxo macro (do insumo ao pedido)
1. Gerente de Cozinha define o **cardápio da semana** (por data).
2. Cardápio referencia pratos → pratos referenciam ingredientes.
3. Sistema checa estoque: se faltar ingrediente, gera **requisição de compra**.
4. Comprador registra compras:
   - opcional: foto do rótulo/contrarrótulo → OCR → pré-preenche dados
   - registra preço, unidade, quantidade, impostos, validade, etc.
5. Sistema calcula:
   - custo por ingrediente
   - custo por prato
   - custo por marmita (porção)
   - sugestão de preço de venda e margem
6. Cliente compra:
   - escolhe data/quantidade
   - paga (Pix/cartão/VR — MVP pode iniciar com Pix e evoluir)
7. Financeiro acompanha:
   - entradas (vendas)
   - saídas (compras + despesas gerais)
   - fluxo de caixa e DRE simplificada

## Fases sugeridas
- **Fase 1 (MVP operacional)**: pedidos + cardápio + estoque básico + custos básicos + financeiro mínimo (caixa/contas).
- **Fase 2**: OCR robusto + custos avançados + relatórios + integrações de pagamento completas.
- **Fase 3**: módulo financeiro pessoal dos sócios (separado dos dados da empresa).
