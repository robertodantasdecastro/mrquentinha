# Context Pack (Resumo Operacional)

## Mapa rapido do repo
- `AGENTS.md` (regras centrais)
- `/home/roberto/.gemini/GEMINI.md` (fonte unica de policy)
- `docs/memory/*` (estado, decisoes, changelog, runbook, roadmap, backlog)
- `scripts/*` (start/smoke/seed/sync/quality/branch_guard/union)
- `workspaces/backend` (API Django/DRF)
- `workspaces/web/portal` (portal institucional)
- `workspaces/web/client` (web cliente)
- `workspaces/web/ui` (UI compartilhada)
- `.agent/workflows/*` (mapa operacional)

## Estado atual
- Concluido: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`, `7.2.1`, `7.2.2`.
- Etapa ativa: `7.2` (proxima subetapa: `T7.2.3`).
- Planejamento mestre ativo: `6.3` (Portal CMS backend-only) e `9.0` (Admin Web MVP).

## Fonte de planejamento
- `docs/memory/REQUIREMENTS_BACKLOG.md`
- `docs/memory/ROADMAP_MASTER.md`
- `docs/memory/BACKLOG.md`
- `.agent/memory/TODO_NEXT.md`

## Portas e scripts
- Backend `8000` -> `scripts/start_backend_dev.sh`
- Portal `3000` -> `scripts/start_portal_dev.sh`
- Client `3001` -> `scripts/start_client_dev.sh`
- Smokes -> `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh`
- Quality -> `scripts/quality_gate_all.sh`
- Sync -> `scripts/sync_memory.sh --check`

## Regra critica
- Sem segredos no repositorio.
- Evitar conflito de portal enquanto `6.2` estiver ativo no Antigravity.
- Proximo passo unico recomendado: `T7.2.3`.
