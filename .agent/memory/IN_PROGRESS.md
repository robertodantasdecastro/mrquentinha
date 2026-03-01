# IN_PROGRESS (lock humano)

Atualize este arquivo no inicio de qualquer sessao em modo escrita.

## Registro atual
- data_hora: 2026-03-01 22:35 UTC
- agente: codex
- branch: main
- etapa: T9.2.7-A5-A2 implementacao inicial AWS no assistente de instalacao/deploy (validacao segura + custos)
- areas_ou_arquivos_tocados:
  - workspaces/backend/src/apps/portal/services.py
  - workspaces/backend/src/apps/portal/views.py
  - workspaces/backend/tests/test_portal_services.py
  - workspaces/backend/tests/test_portal_api.py
  - workspaces/web/admin/src/components/modules/InstallAssistantPanel.tsx
  - workspaces/web/admin/src/lib/api.ts
  - workspaces/web/admin/src/types/api.ts
  - docs/10-plano-mvp-cronograma.md
  - docs/11-plano-cloud-aws-google-e-testes-operacionais.md
  - docs/adr/0016-installer-aws-validacao-segura-e-custos.md
  - docs/memory/CHANGELOG.md
  - docs/memory/DECISIONS.md
  - docs/memory/PROJECT_STATE.md
  - .agent/memory/CONTEXT_PACK.md
  - .agent/memory/TODO_NEXT.md
  - .agent/memory/IN_PROGRESS.md
- objetivo_imediato: entregar primeira iteracao AWS no wizard com credenciais seguras, validacao guiada e custos no Web Admin.
- proximo_comando: consolidar docs/memory, quality gate e preparar commit da trilha AWS inicial.

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
