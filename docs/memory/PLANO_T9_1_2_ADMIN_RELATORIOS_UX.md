# Plano T9.1.2 - Admin Web (Relatorios/Exportacoes + UX/IX)

Data: 2026-02-25

## Objetivo
Entregar relatorios e exportacoes no Admin Web com cobertura de **producao, compras e financeiro**, garantindo **fluxo de caixa global** e **relacionamento consistente entre modulos**, sem redundancias ou lacunas. Em paralelo, **melhorar toda a UX/IX do Admin**, incluindo navegacao por modulo (home/landing por modulo), menus proprios e comunicacao visual clara por estados de movimentacao.

## Respostas do solicitante (registro)
1. Incluir **producao e compras**, com relacionamento entre todos os modulos para fluxo de caixa global, sem erros, redundancias ou esquecimentos.
2. Exportacao: escolher o melhor formato (priorizar CSV; XLSX se houver alto valor para o usuario).
3. Incluir **graficos** e **repensar UX/IX** do Admin: cada modulo deve funcionar como hotpage com menu proprio, navegacao personalizada e interrelacionamento de servicos; usar cores para destacar estados das movimentacoes.

## Escopo funcional (Relatorios/Exportacoes)
1. Relatorios financeiros globais
- Fluxo de caixa por periodo (entradas/saidas) com origem (`ORDER`, `PURCHASE`, `AR`, `AP`).
- Recebiveis (AR) por status e periodo.
- Pagaveis (AP) por status e periodo.
- Conciliacao por metodo de pagamento e provider.

2. Relatorios operacionais
- Producoes por dia/periodo (volume, pratos, custos estimados).
- Compras por periodo, fornecedor, item e impacto financeiro.
- Pedidos por status, metodo de pagamento e canal.

3. Relacionamento entre modulos (consistencia)
- Financeiro sempre referenciar origem via `reference_type` + `reference_id`.
- Evitar duplicidade com idempotencia por referencia.
- Garantir que compras gerem AP/Caixa e pedidos gerem AR/Caixa, sem lacunas.

4. Exportacoes
- CSV como padrao.
- XLSX opcional quando houver valor (ex.: multiplas abas, graficos ou leitura gerencial).
- Exportacao com filtros aplicados e metadata no arquivo.

## Escopo UX/IX (Admin)
1. Navegacao por modulo (hotpage)
- Cada modulo com landing propria (home do modulo).
- Menu contextual por modulo, com rotas e acoes especificas.
- Navegacao consistente entre modulos com trilha de contexto.

2. Visual e interacao
- Cores de estado padronizadas para movimentacoes (ap/ ar/ pedidos/ compras/ producao).
- Destaque de status criticos (atrasos, pendencias, divergencias).
- Tabelas com filtros, resumo e totalizadores.

3. Graficos
- Graficos simples (linha/coluna/pizza) por periodo.
- Totais e variacoes vs periodo anterior.

4. Usabilidade
- Feedbacks claros de carregamento/erro.
- Acessibilidade basica (contraste, foco, teclas).

## Entregaveis
1. Backend
- Selectors e services para relatorios.
- Endpoints para relatorios + export.
- Permissoes RBAC por relatorio.
- Testes unitarios e API.

2. Admin Web
- Nova area de Relatorios.
- Filtros, tabelas e graficos.
- Fluxo de exportacao.
- Novo modelo de navegacao por modulo.
- Atualizacao de tokens de cor para estados.

3. Documentacao
- Atualizar `docs/memory/CHANGELOG.md`.
- Atualizar `docs/memory/PROJECT_STATE.md` e `.agent/memory/*` quando houver mudancas de codigo/fluxo.
- ADR somente se houver mudanca arquitetural.

## Criterios de aceite
- Smokes e testes passando.
- Exportacao consistente com filtros.
- Relatorios cruzando modulos sem divergencia de totais.
- UX/IX com navegacao modular e cores de estados padronizadas.
- Docs e memoria atualizadas.

## Plano de execucao (macro)
1. Mapear relatorios e campos necessarios por modulo.
2. Definir endpoints e contratos de resposta.
3. Implementar selectors/services no backend.
4. Implementar endpoints e exportacao.
5. Implementar UI de relatorios com filtros + graficos.
6. Refatorar navegacao por modulo (hotpages + menus).
7. Ajustar tokens de cores de estado e aplicacao em telas.
8. Testar e atualizar docs/memoria.

