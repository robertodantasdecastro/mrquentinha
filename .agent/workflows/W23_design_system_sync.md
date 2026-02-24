---
id: W23
title: Sync do Design System
description: Auditar portal/client para garantir uso de ui/ + tokens e registrar gaps.
inputs:
  - escopo (portal|client|ambos)
outputs:
  - docs/memory/DESIGN_SYSTEM_STATUS.md
commands:
  - ler GEMINI.md e AGENTS.md
  - auditar componentes/tokens consumidos por portal/client
  - identificar gaps de padronizacao e divergencias
  - atualizar docs/memory/DESIGN_SYSTEM_STATUS.md
quality_gate:
  - uso consistente de ui/TemplateProvider/tokens
memory_updates:
  - docs/memory/DESIGN_SYSTEM_STATUS.md
---

# W23 - Sync do Design System

## Entrega
Gerar `docs/memory/DESIGN_SYSTEM_STATUS.md` com:
1. estado atual por app;
2. gaps e prioridade de correcao;
3. plano curto de alinhamento.
