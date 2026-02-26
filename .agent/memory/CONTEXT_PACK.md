# Context Pack (Resumo Operacional)

## Mapa rapido do repo
- `AGENTS.md` (regras centrais)
- `/home/roberto/.gemini/GEMINI.md` (fonte unica de policy)
- `docs/memory/*` (estado, decisoes, changelog, runbook, roadmap, backlog)
- `scripts/*` (start/smoke/seed/sync/quality/branch_guard/union)
- `workspaces/backend` (API Django/DRF)
- `workspaces/web/portal` (portal institucional)
- `workspaces/web/client` (web cliente)
- `workspaces/web/admin` (admin web de gestao)
- `workspaces/web/ui` (UI compartilhada)
- `.agent/workflows/*` (mapa operacional)

## Estado atual
- Concluido: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`, `7.2.1`, `7.2.2`, `7.2.3`, `6.3.1`, `6.1.1`, `9.0.1`, `9.0.2`, `9.0.3`, `9.1.1`, `9.1.2`, `T9.1.1-HF1`, `T9.1.1-HF2`, `T9.1.1-HF3`, `T9.1.1-HF4`.
- Etapa ativa: `6.2` (ownership Antigravity para consolidacao visual do portal).
- Proxima subetapa recomendada para Codex: `T6.3.2` (integracao CMS no portal apos lock visual de `T6.2.1`).
- Entrega parcial de `T6.3.2` concluida em 26/02/2026: Admin Web ganhou modulo `Portal CMS` com selecao de template ativo e acao de publicacao da configuracao.
- Hotfix mais recente: rotas diretas do Admin (`/modulos` e `/prioridades`) corrigidas com redirect para as ancoras da home, eliminando 404 em acesso por URL direta.
- Fechamento T9.1.2: relatorios ativos no Admin com exportacao CSV por modulo (Pedidos/Compras/Producao/Financeiro/Relatorios), filtro por periodo e rotulos pt-BR de status operacionais.
- Ajuste UX: menus dos modulos filtram blocos por servico (modo completo ou foco) e dashboard do Admin indica etapa 9.1 concluida.

## Fonte de planejamento
- `docs/memory/REQUIREMENTS_BACKLOG.md`
- `docs/memory/ROADMAP_MASTER.md`
- `docs/memory/BACKLOG.md`
- `.agent/memory/TODO_NEXT.md`

## Portas e scripts
- Backend `8000` -> `scripts/start_backend_dev.sh`
- Portal `3000` -> `scripts/start_portal_dev.sh`
- Client `3001` -> `scripts/start_client_dev.sh`
- Admin `3002` -> `scripts/start_admin_dev.sh`
- Proxy local `8088` -> `scripts/start_proxy_dev.sh`
- Smokes -> `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh`, `scripts/smoke_proxy_dev.sh`
- Quality -> `scripts/quality_gate_all.sh`
- Sync -> `scripts/sync_memory.sh --check`

## Regra critica
- Sem segredos no repositorio.
- Evitar conflito de portal enquanto `6.2` estiver ativo no Antigravity.
- Branch Codex por tarefa (`main-etapa-*`) e merge rapido de volta em `main` apos quality gate.
