# Backlog Priorizado (P0/P1/P2)

Referencia: 25/02/2026.

## Regras de execucao
- Branch policy:
  - Codex: `main` e `main-etapa-*`
  - Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`
  - Union: `Antigravity_Codex`
- Prefixo de IDs:
  - `T7.*` pagamentos/client
  - `T6.*` portal/cms/infra
  - `T9.*` admin web gestao
  - `T8.*` financas pessoais

## Concluidas recentes
- [x] `T7.2.1` payment intents com idempotencia.
- [x] `T7.2.2` webhook de pagamento + reconciliacao `AR/Cash/Ledger`.
- [x] `T7.2.3` checkout online no client com intents por metodo e polling de status.
- [x] `T6.3.1` Portal CMS backend-only (Config/Sections + API publica/admin).
- [x] `T9.0.1` Admin Web foundation (shell + auth + dashboard inicial).
- [x] `T9.0.2` Admin Web operacional (Pedidos, Financeiro, Estoque).

## P0 (critico - receita/operacao)

### T6.3.1 (CONCLUIDA)
- Objetivo: Portal CMS backend-only (Config + Sections + API publica/admin).
- Status: concluida em 25/02/2026.
- Escopo: backend + docs.
- Conflito Codex x Antigravity: medio (intersecao funcional com portal 6.2).
- Branch sugerida: `main-etapa-6.3-PortalCMS-BackendOnly`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.0.1 (CONCLUIDA)
- Objetivo: Admin Web foundation (auth shell + dashboard inicial).
- Status: concluida em 25/02/2026.
- Escopo: admin web novo workspace.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-9.0-AdminWeb-Foundation`.
- DoD:
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/sync_memory.sh --check`

### T9.0.2 (CONCLUIDA)
- Objetivo: Admin Web MVP operacional (Pedidos, Financeiro, Estoque).
- Status: concluida em 25/02/2026.
- Escopo: admin + backend.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-9.0-AdminWeb-CoreOps`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.0.3 (P0)
- Objetivo: expandir o Admin com dashboard consolidado e baseline de Cardapio/Compras/Producao.
- Escopo: admin + backend.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-9.0-AdminWeb-Expansion`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

## P1 (escala/UX)

### T6.2.1 (P1)
- Objetivo: consolidar template `letsfit-clean` no portal.
- Escopo: portal + ui.
- Conflito Codex x Antigravity: alto (ownership Antigravity).
- Branch sugerida:
  - Antigravity: `AntigravityIDE/etapa-6.2-PortalTemplateLetsFit`
  - Codex: somente suporte de integracao via `Antigravity_Codex` quando liberado.

### T6.3.2 (P1)
- Objetivo: integrar CMS no portal (render por template/page).
- Escopo: portal + backend.
- Conflito Codex x Antigravity: alto.
- Branch sugerida: `main-etapa-6.3-PortalCMS-Integracao`.

### T9.1.1 (P1)
- Objetivo: Admin Web completo (modulos 1..10 do epico de gestao).
- Escopo: admin + backend + relatorios.
- Conflito Codex x Antigravity: medio/alto.
- Branch sugerida: `main-etapa-9.1-AdminWeb-Completo`.

### T9.1.2 (P1)
- Objetivo: exportacoes CSV/Excel e graficos no Admin.
- Escopo: admin + API relatorios.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-9.1-AdminWeb-Relatorios`.

## P2 (roadmap e hardening)

### T6.1.1 (P2)
- Objetivo: Nginx/proxy local (www/admin/api/app) com runbook de operacao.
- Escopo: infra + docs.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-6.1-NginxLocal`.

### T8.0.1 (P2)
- Objetivo: discovery de financas pessoais com segregacao LGPD.
- Escopo: docs + arquitetura + backlog.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-8.0-FinancasPessoais-Discovery`.

### T8.1.1 (P2)
- Objetivo: MVP tecnico de segregacao por usuario/colaborador.
- Escopo: backend + auth + privacidade.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-8.1-FinancasPessoais-MVP`.
