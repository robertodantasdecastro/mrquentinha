---
description: Gate unico de qualidade para backend, frontends e smoke de stack antes de merge/release.
---

# Workflow 04 - Quality Gate

1. Backend:
   - `cd workspaces/backend && source .venv/bin/activate && make lint && make test`
2. Root:
   - `make test`
   - `pytest`
3. Portal:
   - `cd workspaces/web/portal && npm run lint && npm run build`
4. Client:
   - `cd workspaces/web/client && npm run lint && npm run build`
5. Smokes:
   - `scripts/smoke_stack_dev.sh`
   - `scripts/smoke_client_dev.sh`
6. Se qualquer etapa falhar, abrir checklist de correcao antes de continuar.
