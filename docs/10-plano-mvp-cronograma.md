# Plano do MVP + cronograma sugerido

> Data de referencia: 23/02/2026

Este cronograma e um **guia** para organizar o desenvolvimento.
A ideia e trabalhar em entregas pequenas e testaveis (sprints semanais ou quinzenais).

## Marcos (milestones) do MVP
1. **M0 — Projeto base**: repos + padroes + scaffold backend + auth
2. **M1 — Catalogo**: ingredientes, pratos, cardapio por dia
3. **M2 — Estoque/Compras**: estoque, requisicao, registro de compra, entrada
4. **M3 — Pedidos**: pedido, itens, status, pagamento MVP
5. **M4 — Financeiro**: AP/AR, despesas, caixa, relatorios minimos
6. **M5 — Piloto**: estabilidade, logs, deploy inicial em EC2

## Sprints sugeridos (6 semanas)
### Semana 1 — M0
- Repositorio + `AGENTS.md` + docs iniciais
- Scaffold backend (Django+DRF) + Postgres
- OAuth Google + JWT
- RBAC basico + healthcheck

### Semana 2 — M1
- CRUD ingredientes
- CRUD pratos (receita)
- Cardapio por dia + itens + preco
- Testes e endpoints versionados

### Semana 3 — M2
- Estoque por ingrediente
- Movimentacoes
- Requisicao de compra (auto ao faltar estoque)
- Registro de compra manual (sem OCR)

### Semana 4 — M3
- Fluxo de pedido do cliente
- Status e historico
- Pagamento MVP (Pix manual / confirmacao interna)

### Semana 5 — M4
- Plano de contas simplificado
- AP/AR com referencia a compras e pedidos
- Fluxo de caixa (movimentos)
- Relatorio simples (receitas x despesas)

### Semana 6 — M5
- Observabilidade minima (logs, health, erros)
- Hardening de seguranca basico
- Deploy EC2 (Nginx + Gunicorn)
- Treino operacional e piloto

## Pos-MVP (planejado)
### Etapa 6 — Portal institucional + distribuicao digital
- Escopo: site institucional, links oficiais, pagina de distribuicao com QR e atalhos.
- Dependencias:
  - MVP operacional validado ate M5;
  - identidade visual e conteudo institucional aprovados;
  - base de deploy e dominios pronta para expansao.

### Etapa 7 — Canais web para clientes (web app/PWA)
- Escopo: experiencia web para consulta, pedido e acompanhamento pelo cliente.
- Dependencias:
  - API de pedidos e pagamentos MVP estavel (M3/M4);
  - observabilidade e deploy estaveis (M5);
  - definicoes de UX de navegacao entre portal, app e web clientes.

### Etapa 8 — Governanca, seguranca e escala dos canais
- Escopo: consolidacao de arquitetura, protecoes, compliance e evolucao de capacidade.
- Dependencias:
  - validacao em producao das etapas 6 e 7;
  - decisoes de segregacao de dados pessoais e politicas LGPD;
  - definicao de estrategia de crescimento (infra, custos e suporte operacional).

## Regras do cronograma
- Cada sprint entrega algo "usavel"
- Nao avanca para OCR/pagamentos completos antes do fluxo operacional estar estavel
- Etapas 6-8 nao alteram o fechamento do MVP operacional (M5)
