# Backlog Priorizado (P0/P1/P2)

Referencia: 25/02/2026.

## Regras de execucao
- Branch policy:
  - Codex: `main` e `main/etapa-*`
  - Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`
  - Union: `Antigravity_Codex`
- Prefixo de IDs:
  - `T7.*` pagamentos/client
  - `T6.*` portal/cms/infra
  - `T9.*` admin web gestao
  - `T8.*` financas pessoais

## P0 (critico - receita/operacao)

### T7.2.1 (P0)
- Objetivo: contrato de pagamentos online (PIX/cartao/VR) com `payment_intent` e idempotencia.
- Escopo: backend.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main/etapa-7.2-PagamentosProvider`.
- DoD:
  - `bash scripts/gemini_check.sh`
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/sync_memory.sh --check`

### T7.2.2 (P0)
- Objetivo: webhook de pagamento + reconciliacao financeira (AR/cash/ledger/close) com reprocessamento seguro.
- Escopo: backend + finance.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main/etapa-7.2-WebhooksConciliacao`.
- DoD:
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

### T7.2.3 (P0)
- Objetivo: checkout online no client (PIX/cartao/VR) com status transacional.
- Escopo: client + contrato API.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main/etapa-7.2-CheckoutClient`.
- DoD:
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/client && npm run lint && npm run build`
  - `bash scripts/smoke_client_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T6.3.1 (P0)
- Objetivo: Portal CMS backend-only (Config + Sections + API publica/admin).
- Escopo: backend + docs.
- Conflito Codex x Antigravity: medio (intersecao funcional com portal 6.2).
- Branch sugerida: `main/etapa-6.3-PortalCMS-BackendOnly`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.0.1 (P0)
- Objetivo: Admin Web foundation (auth shell + dashboard inicial).
- Escopo: admin web novo workspace.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main/etapa-9.0-AdminWeb-Foundation`.
- DoD:
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/sync_memory.sh --check`

### T9.0.2 (P0)
- Objetivo: Admin Web MVP operacional (Pedidos, Financeiro, Estoque).
- Escopo: admin + backend.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main/etapa-9.0-AdminWeb-CoreOps`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

## P1 (escala/UX)

### T6.2.1 (P1)
- Objetivo: consolidar template `letsfit-clean` no portal.
- Escopo: portal + ui.
- Conflito Codex x Antigravity: alto (ownership Antigravity).
- Branch sugerida:
  - Antigravity: `AntigravityIDE/etapa-6.2-PortalTemplateLetsFit`
  - Codex: somente suporte de integracao via `Antigravity_Codex` quando liberado.
- DoD:
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/portal && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T6.3.2 (P1)
- Objetivo: integrar CMS no portal (render por template/page).
- Escopo: portal + backend.
- Conflito Codex x Antigravity: alto.
- Branch sugerida: `main/etapa-6.3-PortalCMS-Integracao`.
- DoD:
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.1.1 (P1)
- Objetivo: Admin Web completo (modulos 1..10 do epico de gestao).
- Escopo: admin + backend + relatorios.
- Conflito Codex x Antigravity: medio/alto.
- Branch sugerida: `main/etapa-9.1-AdminWeb-Completo`.
- DoD:
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.1.2 (P1)
- Objetivo: exportacoes CSV/Excel e graficos no Admin.
- Escopo: admin + API relatorios.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main/etapa-9.1-AdminWeb-Relatorios`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run build`
  - `bash scripts/sync_memory.sh --check`

## P2 (roadmap e hardening)

### T6.1.1 (P2)
- Objetivo: Nginx/proxy local (www/admin/api/app) com runbook de operacao.
- Escopo: infra + docs.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main/etapa-6.1-NginxLocal`.
- DoD:
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T8.0.1 (P2)
- Objetivo: discovery de financas pessoais com segregacao LGPD.
- Escopo: docs + arquitetura + backlog.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main/etapa-8.0-FinancasPessoais-Discovery`.
- DoD:
  - `bash scripts/gemini_check.sh`
  - `bash scripts/sync_memory.sh --check`

### T8.1.1 (P2)
- Objetivo: MVP tecnico de segregacao por usuario/colaborador.
- Escopo: backend + auth + privacidade.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main/etapa-8.1-FinancasPessoais-MVP`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make test`
  - `bash scripts/sync_memory.sh --check`
