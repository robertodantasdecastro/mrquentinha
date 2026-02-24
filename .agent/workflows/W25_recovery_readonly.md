---
id: W25
title: Recovery Read-Only
description: Padronizar recuperacao de contexto em modo leitura, sem alteracoes no projeto.
inputs:
  - incidente (travamento|divergencia|queda)
outputs:
  - docs/memory/RECOVERY_TEMPLATE.md
commands:
  - ler AGENTS.md, GEMINI.md e docs/memory essenciais
  - coletar estado git/processos/ports/logs em modo read-only
  - mapear divergencias docs vs implementacao
  - registrar diagnostico e plano de recuperacao
  - atualizar docs/memory/RECOVERY_TEMPLATE.md
quality_gate:
  - zero alteracao de codigo durante diagnostico
memory_updates:
  - docs/memory/RECOVERY_TEMPLATE.md
  - docs/memory/RUNBOOK_DEV.md (secao de recovery)
---

# W25 - Recovery Read-Only

## Entrega
1. Gerar `docs/memory/RECOVERY_TEMPLATE.md` com checklist padrao.
2. Atualizar `RUNBOOK_DEV.md` com fluxo de recovery read-only.
3. Reportar diagnostico, riscos e plano A/B/C sem alterar codigo.
