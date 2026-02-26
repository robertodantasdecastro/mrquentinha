# IN_PROGRESS (lock humano)

Atualize este arquivo no inicio de qualquer sessao em modo escrita.

## Registro atual
- data_hora: 2026-02-26 05:20
- agente: codex
- branch: main
- etapa: T9.1.3-A6 captura/upload de imagens de compra e OCR (concluida)
- areas_ou_arquivos_tocados:
  - workspaces/backend/src/apps/ocr_ai/services.py
  - workspaces/backend/src/apps/ocr_ai/serializers.py
  - workspaces/backend/src/apps/procurement/views.py
  - workspaces/backend/tests/test_ocr_api.py
  - workspaces/backend/tests/test_procurement_api.py
  - workspaces/web/admin/src/components/modules/ProcurementOpsPanel.tsx
  - workspaces/web/admin/src/components/modules/DishCompositionPanel.tsx
  - workspaces/web/admin/src/lib/api.ts
  - workspaces/web/admin/src/types/api.ts
  - docs/memory/CHANGELOG.md
  - docs/memory/PROJECT_STATE.md
  - .agent/memory/CONTEXT_PACK.md
  - .agent/memory/TODO_NEXT.md
  - .agent/memory/IN_PROGRESS.md
- objetivo_imediato: consolidar captura/upload por camera nas compras e garantir persistencia das fotos usadas no OCR.
- proximo_comando: iniciar T8.0.1 (discovery de financas pessoais com segregacao de escopo).

## Registro anterior (manter historico curto)
- data_hora: 2026-02-26 03:35
- agente: codex
- branch: main
- etapa: T9.1.3-A5 fotos dinamicas no cardapio (concluida)
- areas_ou_arquivos_tocados:
  - workspaces/backend/src/apps/catalog/management/commands/sync_catalog_photos.py
  - workspaces/backend/src/apps/catalog/serializers.py
  - workspaces/backend/src/apps/catalog/selectors.py
  - workspaces/backend/src/apps/catalog/views.py
  - workspaces/backend/tests/test_catalog_photo_sync_command.py
  - workspaces/backend/tests/test_catalog_api.py
  - workspaces/web/portal/src/components/CardapioList.tsx
  - workspaces/web/client/src/components/MenuDayView.tsx
  - workspaces/web/client/src/types/api.ts
  - workspaces/mobile/brand/contentApi.ts
  - docs/memory/CHANGELOG.md
  - docs/memory/PROJECT_STATE.md
  - .agent/memory/CONTEXT_PACK.md
  - .agent/memory/TODO_NEXT.md
  - .agent/memory/IN_PROGRESS.md
- objetivo_imediato: consolidar ciclo completo do cardapio com fotos dinamicas de pratos/insumos para portal, client e contrato mobile.
- proximo_comando: iniciar discovery de escopo e requisitos da T8.0.1.
