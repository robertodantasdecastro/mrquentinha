# IN_PROGRESS (lock humano)

Atualize este arquivo no inicio de qualquer sessao em modo escrita.

## Registro atual
- data_hora: 2026-03-01 23:25 UTC
- agente: codex
- branch: main
- etapa: T9.2.7-A5-A2-HF1 links guiados no Portal CMS + guia de testes manuais do instalador
- areas_ou_arquivos_tocados:
  - workspaces/web/admin/src/app/modulos/portal/sections.tsx
  - docs/12-guia-testes-instalacao-manual.md
  - docs/11-plano-cloud-aws-google-e-testes-operacionais.md
  - docs/memory/CHANGELOG.md
  - docs/memory/DECISIONS.md
  - docs/memory/PROJECT_STATE.md
  - .agent/memory/CONTEXT_PACK.md
  - .agent/memory/TODO_NEXT.md
  - .agent/memory/IN_PROGRESS.md
- objetivo_imediato: concluir melhoria de UX operacional no Portal CMS e fechar guia/manual de teste do instalador com validacao automatizada.
- proximo_comando: executar quality gate da trilha (lint/build/testes backend + check workflow) e preparar commit.

## Registro anterior (manter historico curto)
- data_hora: 2026-02-26 06:05
- agente: codex
- branch: main
- etapa: T9.1.3-A7 ciclo operacional completo (linha de producao + dashboard realtime) (concluida)
- areas_ou_arquivos_tocados:
  - workspaces/backend/src/apps/orders/models.py
  - workspaces/backend/src/apps/orders/services.py
  - workspaces/backend/src/apps/orders/views.py
  - workspaces/backend/src/apps/orders/urls.py
  - workspaces/backend/src/apps/orders/migrations/0004_alter_order_status.py
  - workspaces/backend/src/apps/procurement/notifications.py
  - workspaces/backend/src/apps/procurement/services.py
  - workspaces/backend/src/apps/production/services.py
  - workspaces/backend/src/apps/ocr_ai/services.py
  - workspaces/web/admin/src/components/AdminFoundation.tsx
  - workspaces/web/admin/src/components/modules/MenuOpsPanel.tsx
  - workspaces/web/admin/src/components/modules/OrdersOpsPanel.tsx
  - workspaces/web/client/src/components/OrderHistoryList.tsx
  - docs/memory/CHANGELOG.md
  - docs/memory/PROJECT_STATE.md
  - .agent/memory/CONTEXT_PACK.md
  - .agent/memory/TODO_NEXT.md
  - .agent/memory/IN_PROGRESS.md
- objetivo_imediato: consolidar ciclo operacional ponta a ponta com alertas de compras, entrega e confirmacao de recebimento.
- proximo_comando: iniciar T8.0.1 (discovery de financas pessoais com segregacao de escopo).
