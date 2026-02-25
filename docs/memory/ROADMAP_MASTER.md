# Roadmap Master

Referencia: 25/02/2026.
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

### Etapas 6.3 e 9.0
- `T6.3.1` concluida: Portal CMS backend-only com Config/Sections, API publica read-only e endpoints admin.
  - Evidencia: `workspaces/backend/src/apps/portal/`, `workspaces/backend/tests/test_portal_api.py`, `workspaces/backend/tests/test_portal_services.py`.
- `T9.0.1` concluida: Admin Web foundation com novo workspace `workspaces/web/admin`.
  - Evidencia: shell inicial, login JWT (`token/refresh/me`) e dashboard base com status operacional.
- `T9.0.2` concluida: Admin Web operacional com modulos de Pedidos, Financeiro e Estoque conectados ao backend.
  - Evidencia: `workspaces/web/admin/src/components/modules/*`, `AdminFoundation` integrado e `scripts/quality_gate_all.sh` em status `OK`.
- `T9.0.3` concluida: Admin Web expansion com baseline de Cardapio, Compras e Producao conectados ao backend.
  - Evidencia: `MenuOpsPanel`, `ProcurementOpsPanel`, `ProductionOpsPanel`, camada API expandida e quality gate completo em `OK`.

## 2) Em progresso

- Etapa ativa de negocio: `9.0` (Admin Web MVP).
- Proxima subetapa cronologica: `T9.1.1` (fluxo completo dos modulos de gestao e trilha de usuarios/RBAC).
- Planejamento tecnico ativo (docs-first):
  - `9.1` Admin Web completo.
  - `6.3.2` Integracao CMS no portal.
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
- Objetivo: portal consumir CMS via API (template/page sections) com fallback seguro.

#### T9.1.2 - Admin Web relatorios e exportacoes
- Objetivo: expandir Admin com relatorios graficos e exportacoes CSV/Excel.

### P2 (roadmap)

#### T6.1.1 - Nginx local e dominios dev
- Objetivo: consolidar proxy local (`www/admin/api/app`) e reduzir friccao de testes integrados.

#### T8.0.1 - Financas pessoais (discovery + desenho)
- Objetivo: definir segregacao de dados e limites de produto para trilha pessoal.
