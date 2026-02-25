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

## 2) Em progresso

- Etapa ativa de negocio: `7.2` (pagamentos online PIX/cartao/VR).
- Planejamento tecnico ativo (docs-first):
  - `6.3` Portal CMS backend-only (contratos e backlog de implementacao).
  - `9.0` Admin Web MVP (gestao interna).
- Observacao de paralelo:
  - Trilha visual do portal `6.2` pode estar em progresso no Antigravity; Codex deve evitar alteracoes concorrentes de layout enquanto houver lock ativo.

## 3) Pendente

### P0 (desbloqueia operacao/receita)

#### T7.2.1 - Payment provider abstraction + intents
- Objetivo: criar contrato de pagamento online (PIX/cartao/VR) com idempotencia por requisicao.
- Escopo: backend + docs.
- Risco de conflito: baixo (Codex).
- Branch padrao:
  - Codex: `main/etapa-7.2-PagamentosProvider`
  - Antigravity: `AntigravityIDE/etapa-7.2-PagamentosProvider`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `bash scripts/gemini_check.sh`
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex`
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: endpoints `/payments/intents`, services provider-agnostic, testes de idempotencia, docs atualizadas.

#### T7.2.2 - Webhooks + conciliacao financeira
- Objetivo: processar callback de provider com reconciliacao em `orders` + `finance` + `ledger` + `close`.
- Escopo: backend + scripts smoke + docs.
- Risco de conflito: medio (ordens/finance podem ter evolucoes paralelas).
- Branch padrao:
  - Codex: `main/etapa-7.2-WebhooksConciliacao`
  - Antigravity: `AntigravityIDE/etapa-7.2-WebhooksConciliacao`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: endpoint de webhook idempotente, fluxo `Payment -> AR/Cash/Ledger`, testes de reprocessamento.

#### T7.2.3 - Checkout client com pagamentos online
- Objetivo: integrar client ao fluxo de intent/status de pagamento online.
- Escopo: client + backend contract tests + docs.
- Risco de conflito: medio (depende de T7.2.1/T7.2.2).
- Branch padrao:
  - Codex: `main/etapa-7.2-CheckoutClient`
  - Antigravity: `AntigravityIDE/etapa-7.2-CheckoutClient`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/client && npm run lint && npm run build`
  - `bash scripts/smoke_client_dev.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: fluxo PIX/cartao/VR no checkout, polling/status, estados de erro e sucesso.

#### T6.3.1 - Portal CMS backend-only (MVP)
- Objetivo: entregar backend do CMS (Config + Sections por template/pagina) com API publica read-only e endpoints de administracao.
- Escopo: backend + docs.
- Risco de conflito: medio (interseca com portal 6.2; evitar mudanca visual no portal nesta tarefa).
- Branch padrao:
  - Codex: `main/etapa-6.3-PortalCMS-BackendOnly`
  - Antigravity: `AntigravityIDE/etapa-6.3-PortalCMS-BackendOnly`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: modelos CMS com `JSONField`, endpoints `/api/v1/cms/public/*` e `/api/v1/cms/admin/*`, testes API.

#### T9.0.1 - Admin Web MVP foundation
- Objetivo: criar app web de gestao (shell + auth + dashboard inicial).
- Escopo: admin web + ui shared + docs.
- Risco de conflito: baixo (novo workspace dedicado).
- Branch padrao:
  - Codex: `main/etapa-9.0-AdminWeb-Foundation`
  - Antigravity: `AntigravityIDE/etapa-9.0-AdminWeb-Foundation`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: rotas base, autenticacao por JWT, dashboard com KPIs/saude operacional.

#### T9.0.2 - Admin Web MVP operacional
- Objetivo: entregar modulos minimos de gestao para operar dia-a-dia (Pedidos, Financeiro, Estoque).
- Escopo: admin web + backend integration + docs.
- Risco de conflito: medio (integra com modulos backend sensiveis).
- Branch padrao:
  - Codex: `main/etapa-9.0-AdminWeb-CoreOps`
  - Antigravity: `AntigravityIDE/etapa-9.0-AdminWeb-CoreOps`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: telas operacionais de lista/acoes com RBAC e trilha minima de auditoria.

### P1 (escala/UX)

#### T6.2.1 - Portal template `letsfit-clean` (consolidacao)
- Objetivo: finalizar template institucional e consolidar no fluxo oficial sem colisao entre agentes.
- Escopo: portal + ui shared + docs.
- Risco de conflito: alto (ownership principal Antigravity).
- Branch padrao:
  - Codex: evitar alteracao direta enquanto lock Antigravity ativo.
  - Antigravity: `AntigravityIDE/etapa-6.2-PortalTemplateLetsFit`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/portal && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: template clean publicado, SEO base e compatibilidade com CMS.

#### T6.3.2 - Integracao CMS no portal
- Objetivo: portal consumir CMS via API (template/page sections).
- Escopo: portal + backend + docs.
- Risco de conflito: alto (intersecao com 6.2).
- Branch padrao:
  - Codex: `main/etapa-6.3-PortalCMS-Integracao`
  - Antigravity: `AntigravityIDE/etapa-6.3-PortalCMS-Integracao`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: portal renderizado por CMS com fallback seguro.

#### T9.1.1 - Admin Web completo por modulos
- Objetivo: expandir Admin Web para todos os modulos (Cardapio, Compras, Producao, Usuarios/RBAC, Portal CMS, Relatorios).
- Escopo: admin + backend + docs.
- Risco de conflito: medio/alto (muitos dominios).
- Branch padrao:
  - Codex: `main/etapa-9.1-AdminWeb-Completo`
  - Antigravity: `AntigravityIDE/etapa-9.1-AdminWeb-Completo`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: modulos 1..10 do epico de gestao com RBAC.

### P2 (roadmap)

#### T6.1.1 - Nginx local e dominios dev
- Objetivo: consolidar proxy local (`www/admin/api/app`) e reduzir friccao de testes integrados.
- Escopo: infra/scripts/docs.
- Risco de conflito: baixo.
- Branch padrao:
  - Codex: `main/etapa-6.1-NginxLocal`
  - Antigravity: `AntigravityIDE/etapa-6.1-NginxLocal`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: configuracao Nginx dev documentada e validada.

#### T8.0.1 - Financas pessoais (discovery + desenho)
- Objetivo: definir segregacao de dados e limites de produto para trilha pessoal.
- Escopo: backend/docs/seguranca.
- Risco de conflito: baixo.
- Branch padrao:
  - Codex: `main/etapa-8.0-FinancasPessoais-Discovery`
  - Antigravity: `AntigravityIDE/etapa-8.0-FinancasPessoais-Discovery`
  - Union: `Antigravity_Codex`
- DoD (comandos):
  - `bash scripts/gemini_check.sh`
  - `bash scripts/sync_memory.sh --check`
- Artefatos esperados: especificacao funcional/LGPD e backlog de implementacao.
