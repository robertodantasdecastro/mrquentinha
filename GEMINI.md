# GEMINI - Global Antigravity

## Politica de Branches (Anti-Conflito)

### Branch principal do Codex
- `BRANCH_CODEX_PRIMARY=feature/etapa-4-orders`
- O Codex trabalha somente na branch principal definida acima.

### Branches do Antigravity
- O Antigravity deve sempre criar e usar branches no padrao:
  - `ag/<tipo>/<slug>`
- Exemplos:
  - `ag/chore/smoke-rbac`
  - `ag/feat/ui-order-history`

### Join branch para integracao
- Integracoes entre trabalho Codex e Antigravity devem ocorrer em:
  - `join/codex-ag`
- A join branch integra mudancas sem reescrever historico das branches originais.

### Regras operacionais obrigatorias
- Nunca trabalhar em branch de outro agente.
- Validar branch no inicio e antes de commit/push com:
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders`
  - `bash scripts/branch_guard.sh --agent antigravity --strict`
  - `bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders`

### Seguranca
- Nao salvar segredos em git.
- `.env` real e credenciais ficam fora de versionamento.
