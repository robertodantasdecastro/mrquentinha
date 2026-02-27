# Roadmap Master

Referencia: 27/02/2026.
Escopo: planejamento mestre consolidado (implementado, em progresso e pendente) com foco em execucao controlada entre Codex e Antigravity.

## 1) Implementado

### Etapas base e operacional
- Etapas `0 -> 4` concluida (bootstrap, scaffold backend, catalogo, estoque/compras, pedidos).
  - Evidencia: `docs/memory/CHANGELOG.md`.
- Etapas `5.0 -> 5.6.3` concluida (finance completo MVP: AP/AR/caixa/ledger/conciliacao/fechamento + relatorios).
  - Evidencia: `docs/memory/CHANGELOG.md`, commits `9512342`, `a317ce7`, `4acf2e1`.
- Etapas `6.0` e `6.0.1` concluida (portal institucional scaffold + hardening de stack/smokes).
  - Evidencia: `docs/memory/CHANGELOG.md`, commits `6674912`, `752ef8f`.
- Etapa `7.0` concluida (web client MVP inicial).
  - Evidencia: `docs/memory/CHANGELOG.md`, commit `d63a3d4`.

### Etapa 7.1 (Auth/RBAC)
- `7.1.1` concluida: escopo de ownership em orders/payments no backend.
  - Evidencia: `docs/memory/CHANGELOG.md`, commit `12a18b6`.
- `7.1.2` concluida: auth real no client (login/register/me/refresh) e remocao do demo.
  - Evidencia: `docs/memory/CHANGELOG.md`, commits `eb5eaa4`, `7482a13`.
- `7.1.3` concluida: fechamento com regressao completa e memoria sincronizada.
  - Evidencia: `docs/memory/CHANGELOG.md`, commit `aaa6653`.

### Etapa 7.2 (Pagamentos online)
- `T7.2.1` concluida: provider abstraction + payment intents + idempotencia.
  - Evidencia: commit `d09fd5d`, testes de intents e ownership.
- `T7.2.2` concluida: webhook idempotente + reconciliacao financeira (`AR/Cash/Ledger`).
  - Evidencia: modelo `PaymentWebhookEvent`, endpoint `/api/v1/orders/payments/webhook/`, testes API de replay e reconciliacao.
- `T7.2.3` concluida: checkout online no client com selecao de metodo (PIX/CARD/VR), criacao de intent e polling de status.
- `T7.2.4-A1` concluida: configuracao multigateway no Portal CMS (Mercado Pago, Efi, Asaas), roteamento por metodo, recebedor CPF/CNPJ, botao de teste no Admin e webhooks dedicados por provider.
  - Evidencia: `workspaces/backend/src/apps/orders/payment_providers.py`, `workspaces/backend/src/apps/orders/views.py`, `workspaces/backend/src/apps/orders/provider_config.py`, `workspaces/web/admin/src/app/modulos/portal/sections.tsx`, `workspaces/backend/tests/test_orders_api.py`.
- `T7.2.4-A2` concluida: roteamento de provider por canal de frontend (`web`/`mobile`) com selecao unica por canal no Portal CMS e propagacao por header para criacao de intent.
  - Evidencia: `workspaces/backend/src/apps/orders/provider_config.py`, `workspaces/backend/src/apps/orders/services.py`, `workspaces/backend/src/apps/orders/views.py`, `workspaces/web/admin/src/app/modulos/portal/sections.tsx`, `workspaces/web/client/src/lib/api.ts`.
- `T7.2.4-A3` concluida: monitoramento realtime do ecossistema e de pagamentos por provider no backend/admin.
  - Evidencia: `workspaces/backend/src/apps/orders/views.py`, `workspaces/backend/src/apps/orders/urls.py`, `workspaces/web/admin/src/app/modulos/monitoramento/sections.tsx`, `workspaces/web/admin/src/components/AdminFoundation.tsx`.

### Etapas 6.3 e 9.0
- `T6.3.1` concluida: Portal CMS backend-only com Config/Sections, API publica read-only e endpoints admin.
  - Evidencia: `workspaces/backend/src/apps/portal/`, `workspaces/backend/tests/test_portal_api.py`, `workspaces/backend/tests/test_portal_services.py`.
- `T6.3.2-A6` concluida: trilha de release mobile no Portal CMS (backend/admin/portal) com endpoint publico `latest`.
  - Evidencia: `workspaces/backend/src/apps/portal/models.py`, `workspaces/backend/src/apps/portal/views.py`, `workspaces/web/admin/src/app/modulos/portal/sections.tsx`, `workspaces/web/portal/src/lib/mobileRelease.ts`.
- `T6.3.2-A7` concluida: novo template web cliente `client-vitrine-fit` (foco em fotos) e governanca de parametros OAuth Google/Apple no Portal CMS.
  - Evidencia: `workspaces/backend/src/apps/portal/services.py`, `workspaces/backend/src/apps/portal/models.py`, `workspaces/web/admin/src/app/modulos/portal/sections.tsx`, `workspaces/web/client/src/components/MenuPage.tsx`, `workspaces/web/client/src/app/conta/page.tsx`.
- `T6.3.2-A9` concluida: exposicao online via Cloudflare no Portal CMS com preview de rotas e toggle de ativacao/desativacao em 1 clique, incluindo atualizacao automatica de URLs/CORS e suporte a modo `hybrid`.
  - Evidencia: `workspaces/backend/src/apps/portal/services.py`, `workspaces/backend/src/apps/portal/views.py`, `workspaces/backend/src/apps/portal/models.py`, `workspaces/web/admin/src/app/modulos/portal/sections.tsx`, `workspaces/backend/tests/test_portal_api.py`, `workspaces/backend/tests/test_portal_services.py`.
- `T6.3.2-A10` concluida: runtime do tunnel Cloudflare controlado pelo Admin (`start/stop/status`) com logs/PID em `.runtime/ops` e monitoramento do servico no endpoint realtime.
  - Evidencia: `workspaces/backend/src/apps/portal/services.py`, `workspaces/backend/src/apps/portal/views.py`, `scripts/cloudflare_tunnel.sh`, `workspaces/backend/src/apps/orders/views.py`, `workspaces/web/admin/src/app/modulos/portal/sections.tsx`.
- `T9.0.1` concluida: Admin Web foundation com novo workspace `workspaces/web/admin`.
  - Evidencia: shell inicial, login JWT (`token/refresh/me`) e dashboard base com status operacional.
- `T9.0.2` concluida: Admin Web operacional com modulos de Pedidos, Financeiro e Estoque conectados ao backend.
  - Evidencia: `workspaces/web/admin/src/components/modules/*`, `AdminFoundation` integrado e `scripts/quality_gate_all.sh` em status `OK`.
- `T9.0.3` concluida: Admin Web expansion com baseline de Cardapio, Compras e Producao conectados ao backend.
  - Evidencia: `MenuOpsPanel`, `ProcurementOpsPanel`, `ProductionOpsPanel`, camada API expandida e quality gate completo em `OK`.
- `T9.2.6-A1` concluida: area de perfil completo do usuario logado no Web Admin em todos os templates, com endpoint autenticado dedicado e suporte a upload de foto/documentos/biometria por foto.
  - Evidencia: `workspaces/backend/src/apps/accounts/models.py`, `workspaces/backend/src/apps/accounts/views.py`, `workspaces/web/admin/src/app/perfil/page.tsx`, `workspaces/backend/tests/test_accounts_api.py`.
- `T9.2.6-A2` concluida: validadores/formatadores globais de formularios no ecossistema web (Admin/Client/Portal), com UX touch para datas e reforco de validacao backend.
  - Evidencia: `workspaces/web/ui/src/components/FormFieldGuard.tsx`, layouts dos 3 frontends, `workspaces/backend/src/apps/accounts/serializers.py`, `workspaces/backend/src/apps/portal/serializers.py`.

### Etapa 8 (Financas pessoais)
- `T8.0.1` concluida: discovery de segregacao de dominio, ownership e requisitos LGPD para trilha pessoal.
  - Evidencia: `docs/memory/T8_0_1_FINANCAS_PESSOAIS_DISCOVERY.md`, `docs/adr/0003-segregacao-financas-pessoais.md`.
- `T8.1.1` concluida: MVP tecnico backend com app `personal_finance`, API autenticada e isolamento por usuario.
  - Evidencia: `workspaces/backend/src/apps/personal_finance/`, `workspaces/backend/tests/test_personal_finance_api.py`.
- `T8.1.2` concluida: LGPD operacional no backend (exportacao, auditoria de acesso e retencao de logs).
  - Evidencia: `workspaces/backend/src/apps/personal_finance/management/commands/purge_personal_audit_logs.py`, `workspaces/backend/tests/test_personal_finance_lgpd.py`.
- `T8.2.1` concluida: discovery da evolucao funcional da trilha pessoal (recorrencia, resumo mensal e importacao CSV MVP).
  - Evidencia: `docs/memory/T8_2_1_FINANCAS_PESSOAIS_EVOLUCAO_DISCOVERY.md`, `docs/adr/0005-evolucao-financas-pessoais-fase-8-2.md`.
- `T8.2.2` concluida: implementacao da evolucao MVP da trilha pessoal (recorrencia idempotente, resumo mensal e importacao CSV preview/confirm).
  - Evidencia: `workspaces/backend/src/apps/personal_finance/`, `workspaces/backend/tests/test_personal_finance_api.py`, `bash scripts/quality_gate_all.sh` em `OK`.

## 2) Em progresso

- Etapa ativa de negocio: `6.2.1` (consolidacao visual do portal no fluxo Antigravity).
- Proxima subetapa cronologica: `T8.2.3` (hardening/operacionalizacao da trilha pessoal apos MVP de evolucao).
- Meta de qualidade ativa: `T9.2.1` (plano e execucao recorrente de testes manuais E2E de todos os modulos).
- Meta de pagamentos ativa: `T7.2.4-A4` (homologacao externa dos tres gateways com credenciais reais, assinatura de webhook por provider e validacao externa).
- Planejamento tecnico ativo (docs-first):
  - `7.2.4-A4` homologacao e hardening de pagamentos multigateway.
  - `8.2.3` hardening da fase de evolucao pessoal.
  - `6.2.1` consolidacao visual do portal (trilha Antigravity).
  - `9.2.1` execucao ciclica do checklist manual com evidencia operacional.
- Observacao de paralelo:
  - Trilha visual do portal `6.2` pode estar em progresso no Antigravity; Codex deve evitar alteracoes concorrentes de layout enquanto houver lock ativo.

## 3) Pendente

### P0 (desbloqueia operacao/receita)

#### T6.3.1 - Portal CMS backend-only (MVP) [CONCLUIDA]
- Objetivo: entregar backend do CMS (Config + Sections por template/pagina) com API publica read-only e endpoints de administracao.
- Status: concluida em 25/02/2026.
- Escopo: backend + docs.
- Risco de conflito: medio (interseca funcionalmente com portal 6.2; sem mexer no layout).
- Branch padrao:
  - Codex: `main-etapa-6.3-PortalCMS-BackendOnly`
  - Antigravity: `AntigravityIDE/etapa-6.3-PortalCMS-BackendOnly`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

#### T9.0.1 - Admin Web MVP foundation [CONCLUIDA]
- Objetivo: criar app web de gestao (shell + auth + dashboard inicial).
- Status: concluida em 25/02/2026.
- Escopo: admin web + ui shared + docs.
- Risco de conflito: baixo.
- Branch padrao:
  - Codex: `main-etapa-9.0-AdminWeb-Foundation`
  - Antigravity: `AntigravityIDE/etapa-9.0-AdminWeb-Foundation`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/sync_memory.sh --check`

#### T9.0.2 - Admin Web MVP operacional [CONCLUIDA]
- Objetivo: entregar modulos minimos de gestao para operar dia-a-dia (Pedidos, Financeiro, Estoque).
- Status: concluida em 25/02/2026.
- Escopo: admin web + backend integration + docs.
- Risco de conflito: medio.
- Branch padrao:
  - Codex: `main-etapa-9.0-AdminWeb-CoreOps`
  - Antigravity: `AntigravityIDE/etapa-9.0-AdminWeb-CoreOps`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

#### T9.0.3 - Admin Web expansion [CONCLUIDA]
- Objetivo: consolidar dashboard de gestao e iniciar modulos de Cardapio, Compras e Producao (baseline MVP).
- Status: concluida em 25/02/2026.
- Escopo: admin web + backend integration + docs.
- Risco de conflito: medio.
- Branch padrao:
  - Codex: `main-etapa-9.0-AdminWeb-Expansion`
  - Antigravity: `AntigravityIDE/etapa-9.0-AdminWeb-Expansion`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

#### T9.1.1 - Admin Web completo por modulos
- Objetivo: evoluir Cardapio/Compras/Producao de baseline para fluxo completo e incluir Usuarios/RBAC.
- Escopo: admin web + backend integration + docs.
- Risco de conflito: medio/alto.
- Branch padrao:
  - Codex: `main-etapa-9.1-AdminWeb-Completo`
  - Antigravity: `AntigravityIDE/etapa-9.1-AdminWeb-Completo`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

### P1 (escala/UX)

#### T6.2.1 - Portal template `letsfit-clean` (consolidacao)
- Ownership: Antigravity.
- Objetivo: finalizar template institucional e consolidar no fluxo oficial.

#### T6.3.2 - Integracao CMS no portal
- Objetivo: portal/client consumir CMS via API (template/page sections + parametros de autenticacao) com fallback seguro.
- Status parcial: `A1..A7`, `A9` e `A10` concluidas (restante tecnico: `A8` para troca de `code` OAuth no backend para login social completo).

#### T7.2.4 - Pagamentos multigateway em tempo real
- Objetivo: suportar Mercado Pago, Efi e Asaas com configuracao central no Portal CMS, fallback por metodo (PIX/CARD/VR) e retorno de status em tempo real para cliente/admin/mobile.
- Status:
  - `A1` concluida em 26/02/2026 (camada de configuracao e rotas de webhook por provider + painel admin).
  - `A2` concluida em 26/02/2026 (provider unico por frontend, roteamento por canal no backend e campos adaptativos no Admin).
  - `A3` concluida em 26/02/2026 (observabilidade operacional por provider com endpoint realtime e modulo de monitoramento no Admin).
  - `A4` pendente (homologacao externa de credenciais, assinatura de webhook real por provider e runbook de producao).
- Evidencias atuais:
  - backend: `apps/orders/payment_providers.py`, `apps/orders/provider_config.py`, `apps/orders/views.py`
  - admin: secao `pagamentos` em `/modulos/portal`
  - client: habilitacao dinamica de metodos por configuracao publica (`payment_providers`)

#### T9.1.2 - Admin Web relatorios e exportacoes
- Objetivo: expandir Admin com relatorios graficos e exportacoes CSV/Excel.

#### T9.2.1 - Campanha de testes manuais E2E
- Objetivo: executar checklist manual completo (portal, client, admin, backend e mobile release), com evidencias e plano de correcao.
- Escopo: QA manual orientado a fluxo de negocio + atualizacao de memoria operacional.
- Evidencia de planejamento: `docs/memory/PLANO_T9_2_1_TESTES_MANUAIS_E2E.md`.

### P2 (roadmap)

#### T6.1.1 - Nginx local e dominios dev
- Objetivo: consolidar proxy local (`www/admin/api/app`) e reduzir friccao de testes integrados.

#### T8.0.1 - Financas pessoais (discovery + desenho) [CONCLUIDA]
- Objetivo: definir segregacao de dados e limites de produto para trilha pessoal.
- Status: concluida em 26/02/2026 (docs-first).
- Evidencia:
  - `docs/memory/T8_0_1_FINANCAS_PESSOAIS_DISCOVERY.md`
  - `docs/adr/0003-segregacao-financas-pessoais.md`

#### T8.1.1 - Financas pessoais (MVP tecnico de segregacao) [CONCLUIDA]
- Objetivo: implementar dominio `personal_finance` com ownership estrito por usuario.
- Escopo: backend + auth + privacidade + testes.
- Status: concluida em 26/02/2026.
- Evidencia:
  - `workspaces/backend/src/apps/personal_finance/`
  - `workspaces/backend/tests/test_personal_finance_api.py`
  - `bash scripts/quality_gate_all.sh` em `OK`.

#### T8.1.2 - Financas pessoais (LGPD operacional) [CONCLUIDA]
- Objetivo: fechar camada operacional de LGPD (retencao, exportacao e trilha de acesso) para dados pessoais.
- Escopo: backend + docs + runbooks.
- Status: concluida em 26/02/2026.
- Evidencia:
  - `workspaces/backend/src/apps/personal_finance/management/commands/purge_personal_audit_logs.py`
  - `workspaces/backend/tests/test_personal_finance_lgpd.py`
  - `bash scripts/quality_gate_all.sh` em `OK`.

#### T8.2.1 - Financas pessoais (discovery de evolucao) [CONCLUIDA]
- Objetivo: definir proxima fase funcional da trilha pessoal (integracoes, UX e escopo de produto).
- Escopo: docs + arquitetura + backlog.
- Status: concluida em 26/02/2026.
- Evidencia:
  - `docs/memory/T8_2_1_FINANCAS_PESSOAIS_EVOLUCAO_DISCOVERY.md`
  - `docs/adr/0005-evolucao-financas-pessoais-fase-8-2.md`

#### T8.2.2 - Financas pessoais (implementacao da evolucao MVP) [CONCLUIDA]
- Objetivo: entregar recorrencia de lancamentos, resumo mensal e importacao CSV com preview/confirmacao.
- Escopo: backend + API + testes + docs.
- Status: concluida em 26/02/2026.
- Evidencia:
  - `workspaces/backend/src/apps/personal_finance/models.py`
  - `workspaces/backend/src/apps/personal_finance/services.py`
  - `workspaces/backend/src/apps/personal_finance/views.py`
  - `workspaces/backend/tests/test_personal_finance_api.py`
  - `bash scripts/quality_gate_all.sh` em `OK`.

#### T8.2.3 - Financas pessoais (hardening pos-MVP)
- Objetivo: consolidar UX/operacao da fase 8.2 com observabilidade, jobs agendados e ajustes de contratos.
- Escopo: backend + operacao + docs.
