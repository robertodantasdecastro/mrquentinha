# Project State (dev)

Referencia de atualizacao: 24/02/2026.

## Etapas
- Concluidas: 0 -> 5.6.3, 6.0, 6.0.1, 7.0.
- Em progresso: 7.1 (Auth/RBAC para cliente real).
- Subetapa concluida em 24/02/2026: 7.1.1 Backend Auth/RBAC (escopo de pedidos/pagamentos por ownership + papeis de gestao).

## Politica de branches (anti-conflito)
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`
- Codex: `main` e `main/etapa-*`.
- Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`.
- Uniao: `Antigravity_Codex` (somente merge/cherry-pick/PR).
- Guard rail: `scripts/branch_guard.sh`.

## Antigravity
- Fonte unica GEMINI (runtime + policy): `/home/roberto/.gemini/GEMINI.md`
- Check de validade GEMINI: `scripts/gemini_check.sh`
- Rules path: `.agent/rules/global.md`
- Espelho topo: `.agent/rules/00_GLOBAL_RULE.md`
- Guia de uso: `.agent/workflows/USAGE_GUIDE.md`
- Mapa oficial: `.agent/workflows/WORKFLOW_MAP.md`

## Modo paralelo
- Regras: `docs/memory/PARALLEL_DEV_RULES.md`
- Lock humano: `.agent/memory/IN_PROGRESS.md`
- Sync obrigatorio: `W21_sync_codex_antigravity`

## Estado por Componente

### Backend (Django)
- **Status:** Operacional (Autenticação JWT, Cartões de Crédito, Mock OCR, Perfis Lojista/Cliente)
- **Banco de Dados:** PostgreSQL (`mrquentinhabd`)
- **App Principal:** `core`, `accounts`, `catalog`, `inventory`, `orders`, `finance`, `production`, `ocr_ai`
- **Cobertura de Testes:** Boa (~85%)

### Web Portal (Next.js - 3000)
- **Status:** Landing page institucional
- **Features:** Estrutura unificada, `CardapioList` dinâmico integrado à API (`/today/` e `/by-date/`).
- **Templates:** Suporte a chaveamento de templates via `NEXT_PUBLIC_PORTAL_TEMPLATE`.
  - Padrões suportados: `classic` e `letsfit-clean`.

### Web Client (Next.js - 3001)

## Workflows adicionais
- `W22_layout_references_audit`
- `W23_design_system_sync`
- `W24_git_comparison_review`
- `W25_recovery_readonly`

## Modulos backend ativos
- `catalog`
- `inventory`
- `procurement`
- `orders`
- `finance`
- `production`
- `ocr_ai`

## Frontends ativos
- Portal (`workspaces/web/portal`) porta `3000`
- Client (`workspaces/web/client`) porta `3001`
- UI shared (`workspaces/web/ui`)

## API backend
- Porta: `8000`
- `GET /` (API index)
- `GET /api/v1/health`
- RBAC hardening ativo por perfil.
- Excecao MVP (read-only publico):
  - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
  - `GET /api/v1/catalog/menus/today/`

## Scripts oficiais
- Start:
  - `scripts/start_backend_dev.sh`
  - `scripts/start_portal_dev.sh`
  - `scripts/start_client_dev.sh`
- Smoke:
  - `scripts/smoke_stack_dev.sh`
  - `scripts/smoke_client_dev.sh`
- Dados:
  - `scripts/seed_demo.sh`
- Qualidade e sync:
  - `scripts/gemini_check.sh`
  - `scripts/quality_gate_all.sh`
  - `scripts/sync_memory.sh`
  - `scripts/branch_guard.sh`
  - `scripts/union_branch_build_and_test.sh`
  - `scripts/sync_gemini_global.sh` (desativado)
  - `scripts/diff_gemini.sh` (snapshot opcional)

## Quickstart
No root (`~/mrquentinha`), em terminais separados:

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Validacao rapida:

```bash
./scripts/smoke_stack_dev.sh
./scripts/smoke_client_dev.sh
```

Pre-commit recomendado:

```bash
bash scripts/gemini_check.sh
bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/quality_gate_all.sh
bash scripts/sync_memory.sh --check
```

## Regra de segredos
- Valores reais apenas em `.env` local (gitignored).
- Repositorio deve conter placeholders em `.env.example`.

## Plano da etapa ativa
- Etapa ativa: 7.1 (Auth/RBAC end-to-end).
- Branch Codex da etapa: main (guard ativo para codex; namespace main/etapa-* indisponivel no repo atual).
- Foco imediato:
  1) client: autenticacao JWT real (sem demo).
  2) fechamento 7.1: quality gate + smokes + docs.
  3) preparacao da etapa 7.2 (pagamentos online) apos concluir 7.1.
