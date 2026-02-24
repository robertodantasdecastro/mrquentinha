---
description: Checkpoint de release para congelar estado validado e opcionalmente publicar tag.
---

# Workflow 06 - Release Checkpoint

1. Rodar workflow de qualidade completo.
2. Confirmar `git status` limpo.
3. Criar tag de checkpoint (ex.: `checkpoint-YYYYMMDD-HHMM`).
4. Publicar tag se aplicavel (`git push origin <tag>`).
5. Registrar checkpoint no `CHANGELOG`.
