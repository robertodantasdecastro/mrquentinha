---
id: W19
title: Release e tag
description: Executar checkpoint de release interna com tag anotada e publicacao segura.
inputs:
  - nome_tag
outputs:
  - release_publicada
commands:
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

## Passos
1. Rodar quality gate completo (W16).
2. Atualizar `CHANGELOG` com nota curta de release.
3. Criar tag anotada.
4. Publicar branch e tag no remoto.

## Criterio de saida
- Tag publicada com qualidade validada.
