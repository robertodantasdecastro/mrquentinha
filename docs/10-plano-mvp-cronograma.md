# Plano do MVP + cronograma sugerido

> Data de referência: 23/02/2026

Este cronograma é um **guia** para organizar o desenvolvimento.
A ideia é trabalhar em entregas pequenas e testáveis (sprints semanais ou quinzenais).

## Marcos (milestones)
1. **M0 — Projeto base**: repos + padrões + scaffold backend + auth
2. **M1 — Catálogo**: ingredientes, pratos, cardápio por dia
3. **M2 — Estoque/Compras**: estoque, requisição, registro de compra, entrada
4. **M3 — Pedidos**: pedido, itens, status, pagamento MVP
5. **M4 — Financeiro**: AP/AR, despesas, caixa, relatórios mínimos
6. **M5 — Piloto**: estabilidade, logs, deploy inicial em EC2

## Sprints sugeridos (6 semanas)
### Semana 1 — M0
- Repositório + `AGENTS.md` + docs iniciais
- Scaffold backend (Django+DRF) + Postgres
- OAuth Google + JWT
- RBAC básico + healthcheck

### Semana 2 — M1
- CRUD ingredientes
- CRUD pratos (receita)
- Cardápio por dia + itens + preço
- Testes e endpoints versionados

### Semana 3 — M2
- Estoque por ingrediente
- Movimentações
- Requisição de compra (auto ao faltar estoque)
- Registro de compra manual (sem OCR)

### Semana 4 — M3
- Fluxo de pedido do cliente
- Status e histórico
- Pagamento MVP (Pix manual / confirmação interna)

### Semana 5 — M4
- Plano de contas simplificado
- AP/AR com referência a compras e pedidos
- Fluxo de caixa (movimentos)
- Relatório simples (receitas x despesas)

### Semana 6 — M5
- Observabilidade mínima (logs, health, erros)
- Hardening de segurança básico
- Deploy EC2 (Nginx + Gunicorn)
- Treino operacional e piloto

## Regras do cronograma
- Cada sprint entrega algo “usável”
- Não avança para OCR/pagamentos completos antes do fluxo operacional estar estável
