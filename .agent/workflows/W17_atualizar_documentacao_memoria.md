---
id: W17
title: Atualizar documentacao e memoria
description: Sincronizar memoria viva e docs operacionais com o estado real do projeto.
inputs:
  - mudancas_realizadas
outputs:
  - docs_sincronizadas
commands:
  - atualizar docs/memory/PROJECT_STATE.md
  - atualizar .agent/memory/TODO_NEXT.md
  - atualizar docs/memory/DECISIONS.md
  - atualizar docs/memory/CHANGELOG.md
quality_gate:
  - docs sem segredos e com estado real validado
memory_updates:
  - aplicacao obrigatoria neste proprio workflow
---

# W17 - Atualizar documentacao/memoria

## Passos
1. Atualizar `PROJECT_STATE` com portas, endpoints e scripts atuais.
2. Atualizar `TODO_NEXT` com fila cronologica objetiva.
3. Atualizar `DECISIONS` com decisoes novas e pendencias.
4. Atualizar `CHANGELOG` com entrega resumida.
5. Revisar diffs para garantir ausencia de segredos.

## Criterio de saida
- Memoria coerente com o estado atual do repositorio.
