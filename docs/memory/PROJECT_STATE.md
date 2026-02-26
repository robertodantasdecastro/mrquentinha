# Project State (dev)

Referencia de atualizacao: 26/02/2026.

## Etapas
- Concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`, `7.2.1`, `7.2.2`, `7.2.3`, `6.3.1`, `6.1.1`, `9.0.1`, `9.0.2`, `9.0.3`, `9.1.1`, `9.1.2`, `9.1.3-A6`, `6.3.2-A3`.
- Em progresso: `6.2` (Portal template no fluxo Antigravity).
- Proxima execucao recomendada (unica): `T8.0.1` (discovery de financas pessoais e segregacao de escopo).

## Planejamento oficial (docs-first)
- Requisitos consolidados: `docs/memory/REQUIREMENTS_BACKLOG.md`
- Roadmap mestre: `docs/memory/ROADMAP_MASTER.md`
- Backlog priorizado: `docs/memory/BACKLOG.md`
- Fila operacional curta: `.agent/memory/TODO_NEXT.md`

## Politica de branches (anti-conflito)
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`
- Codex: `main` e `main-etapa-*`.
- Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`.
- Uniao: `Antigravity_Codex` (somente merge/cherry-pick/PR).
- Guard rail: `scripts/branch_guard.sh`.

## Antigravity / GEMINI
- Fonte unica GEMINI (runtime + policy): `/home/roberto/.gemini/GEMINI.md`
- Validacao obrigatoria: `bash scripts/gemini_check.sh`
- Rules path: `.agent/rules/global.md`
- Espelho topo: `.agent/rules/00_GLOBAL_RULE.md`
- Guia de uso: `.agent/workflows/USAGE_GUIDE.md`
- Mapa oficial: `.agent/workflows/WORKFLOW_MAP.md`

## Modo paralelo
- Regras: `docs/memory/PARALLEL_DEV_RULES.md`
- Lock humano: `.agent/memory/IN_PROGRESS.md`
- Sync obrigatorio: `W21_sync_codex_antigravity`
- Observacao: se `6.2 portal template` estiver ativo no Antigravity, Codex evita alteracao concorrente de layout no portal.

## Estado por componente

### Backend (Django)
- Status: operacional (Auth JWT, Finance MVP completo, OCR mock, nutricao, producao, relatorios).
- Banco: PostgreSQL (`mrquentinhabd`).
- Modulos ativos: `core`, `accounts`, `catalog`, `inventory`, `procurement`, `orders`, `finance`, `production`, `ocr_ai`, `portal`.
- Pagamentos online (`7.2.1` + `7.2.2` + `7.2.3`):
  - `PaymentIntent` persistido com idempotencia por pagamento/chave.
  - provider abstraction inicial (`mock`) com payload de intent para PIX/CARD/VR.
  - webhook idempotente com reconciliacao para `AR/Cash/Ledger`.
  - criacao de pedido com `payment_method` (PIX/CARD/VR) para acionar checkout online por intent.
  - eventos de webhook persistidos em `PaymentWebhookEvent` para replay seguro por `provider + event_id`.

### Web Portal (Next.js - 3000)
- Status: institucional em evolucao de template (`classic` + `letsfit-clean`).
- Integracao: cardapio por API (`/today/` e `/by-date/`).
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A2`): consumo de `active_template` do CMS em runtime (server-side).
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A2-HF1`): fallback automatico de API no cardapio para host atual (`:8000`) quando variavel de ambiente nao estiver definida.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A3`): template LetsFit passou a consumir secoes dinamicas do CMS (`hero`, `benefits`, `categories`, `kit`, `how_to_heat`, `faq`) incluindo fotos/links via `body_json`.
- Risco de conflito: alto em paralelo com trilha Antigravity de template.

### Web Client (Next.js - 3001)
- Status: auth real concluida (`register/token/refresh/me`).
- Pedido/historico: escopo autenticado sem demo.
- Checkout online concluido com intents por metodo (PIX/CARD/VR), painel de instrucoes e polling via `intent/latest`.
- Atualizacao concluida em 26/02/2026 (`T7.2.3-HF1`): fallback automatico de API para host atual (`:8000`) e mensagem de erro de rede padronizada.

### Admin Web (Next.js - 3002)
- Status: `T9.1.2` concluida (relatorios/exportacoes + UX/IX modular).
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF1`): correcoes de `onChange` para evitar crash client-side no login e ajuste de `allowedDevOrigins` no Next 16 para acesso em `10.211.55.21:3002`.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF2`): liberacao de CORS do backend para origem `:3002`, fallback automatico da API no Admin Web e exibicao de erros diretamente no card de login.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF3`): padronizacao visual global com cores de status (success/warning/danger/info) e aplicacao da logo oficial (PNG original) no Admin Web, Portal e Client.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF4`): rotas diretas `/modulos` e `/prioridades` com redirect para `/#modulos` e `/#prioridades`, evitando erro 404 em acesso por URL/bookmark (substituido pela navegacao por hotpages).
- Entrega atual: modulos de Pedidos/Financeiro/Estoque/Cardapio/Compras/Producao e Usuarios/RBAC estaveis, com hotpages, menus contextuais, graficos e relatorios/exportacoes CSV com filtros por periodo.
- Atualizacao concluida em 25/02/2026 (`T9.1.2`): exportacoes por modulo (Pedidos/Compras/Producao/Financeiro), traducao pt-BR de status operacionais e consolidacao do modulo de Relatorios como ativo.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A1`): modulo `Portal CMS` no Admin Web para selecionar template ativo existente e publicar configuracao de portal.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A2`): Portal Web passou a consumir `active_template` do CMS em runtime (server-side), refletindo mudancas do Admin sem rebuild por variavel de ambiente.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A1`): Cardapio ganhou secao de composicao (ingredientes + prato com receita) para viabilizar ciclo completo de operacao.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A2`): Compras ganhou registro operacional de compra com itens (entrada em estoque), alem da geracao de requisicao por cardapio com seletor.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A3`): Cardapio ganhou padrao de periodos (Manha/Cafe, Almoco, Jantar, Lanche) para organizacao de menus diarios.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A4`): modulo Cardapio finalizado com edicao de insumos/pratos e composicao completa no Admin.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A5`): fotos dinamicas de pratos e insumos sincronizadas no banco e expostas no endpoint de cardapio (incluindo composicao com `image_url` por insumo).
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A6`): compras/OCR com captura/upload de imagens no Admin, persistencia de fotos no destino apos OCR aplicado e icones visuais por item/comprovante.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A3`): modulo Portal CMS ganhou editor de secoes dinamicas (template/pagina/body_json) e a composicao ganhou upload de fotos para insumos e pratos.
- Workspace ativo: `workspaces/web/admin`.
- Proximo alvo: iniciar `T8.0.1` (discovery de financas pessoais e segregacao LGPD).

## Portas e scripts oficiais
- Backend: `8000` -> `scripts/start_backend_dev.sh`
- Portal: `3000` -> `scripts/start_portal_dev.sh`
- Client: `3001` -> `scripts/start_client_dev.sh`
- Admin Web: `3002` -> `scripts/start_admin_dev.sh`
- Proxy local Nginx: `8088` -> `scripts/start_proxy_dev.sh`
- Smoke: `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh`, `scripts/smoke_proxy_dev.sh`
- Seed: `scripts/seed_demo.sh`
- Quality gate: `scripts/quality_gate_all.sh`
- Sync docs: `scripts/sync_memory.sh --check`

## Endpoints chave
- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/token/`
- `POST /api/v1/accounts/token/refresh/`
- `GET /api/v1/accounts/me/`
- `GET /api/v1/accounts/roles/`
- `GET /api/v1/accounts/users/`
- `GET /api/v1/accounts/users/<id>/`
- `POST /api/v1/accounts/users/<id>/roles/`
- Publicos read-only de menu:
  - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
  - `GET /api/v1/catalog/menus/today/`
- Pagamentos intent:
  - `POST /api/v1/orders/payments/<id>/intent/`
  - `GET /api/v1/orders/payments/<id>/intent/latest/`
- Webhook pagamentos:
  - `POST /api/v1/orders/payments/webhook/` (`X-Webhook-Token`)
- Portal CMS publico:
  - `GET /api/v1/portal/config/`
  - `GET /api/v1/portal/config/version`

## Plano da etapa ativa
- Trilha principal: `9.1 Admin Web completo` (concluida).
- T9.0.1 concluida (Admin Web foundation: shell + auth + dashboard inicial).
- T9.0.2 concluida (Admin Web operacional: Pedidos, Financeiro e Estoque conectados ao backend).
- T9.0.3 concluida (Admin Web expansion: baseline de Cardapio, Compras e Producao).
- T9.1.1 concluida (modulo Usuarios/RBAC entregue com endpoints admin + painel no Admin Web).
- T9.1.1-HF1 concluida (hotfix de login no Admin Web: crash client-side ao digitar usuario + ajuste de allowedDevOrigins para acesso via IP).
- T9.1.1-HF2 concluida (hotfix de login no Admin Web: CORS backend para `:3002` + fallback de API base + feedback inline de erro no formulario).
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF3`): padronizacao visual global com cores de status (success/warning/danger/info) e aplicacao da logo oficial (PNG original) no Admin Web, Portal e Client.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF4`): rotas diretas `/modulos` e `/prioridades` no Admin Web agora redirecionam para `/#modulos` e `/#prioridades`, evitando erro 404 em acesso por URL/bookmark.
- T9.1.2 concluida (relatorios/exportacoes no Admin Web com filtro por periodo e exportacao CSV funcional por modulo).
- Proxima subetapa unica: executar `T8.0.1` (descoberta de financas pessoais e segregacao).
- Trilhas correlatas apos 9.1: `T6.2.1` (Antigravity) e `T8.0.1`.
