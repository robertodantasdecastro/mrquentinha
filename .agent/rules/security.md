# Regras de Seguranca

- Proibido versionar segredos: senhas, tokens, chaves privadas, credenciais de banco e API keys.
- `.env` real deve permanecer local e gitignored.
- Versionar apenas `.env.example` com placeholders (ex.: `CHANGE_ME`).
- Nao incluir dados sensiveis em documentacao, changelog, commits ou pull requests.
- Revisar `git diff` antes de commit para evitar vazamento de informacao sensivel.
- Em logs e exemplos de comando, mascarar dados confidenciais.
