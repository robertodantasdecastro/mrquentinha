# Regras Operacionais do Projeto

- Ler sempre: `AGENTS.md`, `docs/memory/PROJECT_STATE.md`, `docs/memory/DECISIONS.md`, `docs/memory/CHANGELOG.md`, `docs/memory/RUNBOOK_DEV.md`.
- Nao comitar segredos; usar apenas placeholders em arquivos de exemplo.
- Executar em passos curtos: implementar -> validar -> commit -> atualizar memoria.
- Manter smokes do stack e client passando.
- Atualizar `docs/memory/PROJECT_STATE.md` em qualquer mudanca de endpoint/script/porta.
- Backend: seguir `services/selectors/serializers/views/urls/tests`.
- Frontend: usar Design System + templates modulares, com visual clean e conteudo dinamico via API.
