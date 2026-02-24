# Regra de Sync (operacional)

- Qualquer mudanca em `workspaces/backend`, `workspaces/web` ou `scripts` aciona sync obrigatorio.
- Antes de agir: ler `AGENTS.md` + memoria oficial (`PROJECT_STATE`, `CHANGELOG`, `DECISIONS`, `RUNBOOK_DEV`, `CONTEXT_PACK`).
- Atualizar Sync Pack em toda mudanca estrutural/operacional.
- Sem segredos no git: `.env` real nunca entra; apenas `.env.example` com placeholders.
- Rodar quality gate antes de commit: backend tests + builds + smokes.
- Confirmar diff sem segredos (`PASSWORD=`, `SECRET_KEY=`, `AKIA`, `-----BEGIN`).
