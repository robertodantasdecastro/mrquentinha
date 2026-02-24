---
id: W19
title: Release e tag
description: Publicar checkpoint de release com branch policy e qualidade completa.
inputs:
  - agente (codex|union)
  - nome_tag
outputs:
  - release_publicada
commands:
  - sed -n '1,220p' /home/roberto/.gemini/GEMINI.md
  - bash scripts/branch_guard.sh --agent <agente> --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - executar W16_auditoria_qualidade
  - atualizar CHANGELOG com release note curta
  - git tag -a <tag> -m "release"
  - git push origin <branch>
  - git push origin <tag>
quality_gate:
  - quality gate completo antes de tag
memory_updates:
  - CHANGELOG com nota de release
---

# W19 - Release/Tag

## Regras
- Ler `/home/roberto/.gemini/GEMINI.md`.
- Branch permitida para release: `main` ou `Antigravity_Codex`.
- Antigravity nao publica release fora do fluxo de integracao.

## Criterio de saida
- Tag publicada com qualidade validada e memoria sincronizada.
