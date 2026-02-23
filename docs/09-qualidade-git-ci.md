# Qualidade, Git e CI

## Branching
Sugestão simples:
- `main` (estável)
- `dev` (integração)
- `feature/<nome>`
- `fix/<nome>`

## Commits
- padrão recomendado: Conventional Commits
  - `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`, `test: ...`

## Ferramentas de qualidade (backend)
- `ruff` (lint)
- `black` (format)
- `mypy` (tipos, opcional mas recomendado)
- `pytest` (testes)
- `coverage` (cobertura)

## Definition of Done (repetindo o essencial)
- testes passam
- lint/format ok
- migrações ok
- docs atualizadas

## CI (quando for para a nuvem)
Mesmo sem Docker, dá para usar GitHub Actions para rodar:
- setup python
- instalar deps
- subir Postgres service (do próprio runner)
- rodar testes
