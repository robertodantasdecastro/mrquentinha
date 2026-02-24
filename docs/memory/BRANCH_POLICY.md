# Branch Policy (Codex x Antigravity x Union)

Atualizado em: 24/02/2026.

## Branches canonicos
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`

## Regra por agente
1. Codex trabalha em:
  - `main`
  - `main/etapa-N-TituloEtapa`
2. Antigravity trabalha em:
  - `AntigravityIDE`
  - `AntigravityIDE/etapa-N-TituloEtapa`
3. Uniao trabalha somente em:
  - `Antigravity_Codex` (merge/cherry-pick/PR)
  - nao usar como branch de desenvolvimento diario.

## Regra de branches por etapa
### Codex
```bash
git checkout main
git checkout -b main/etapa-7.1-Auth-RBAC main
# ... desenvolvimento ...
git checkout main
git merge --no-ff main/etapa-7.1-Auth-RBAC
```

### Antigravity
```bash
git checkout AntigravityIDE
git checkout -b AntigravityIDE/etapa-7.1-Auth-RBAC AntigravityIDE
# ... desenvolvimento ...
git checkout AntigravityIDE
git merge --no-ff AntigravityIDE/etapa-7.1-Auth-RBAC
```

## Workflow de uniao (main + AntigravityIDE)
Comando oficial:
```bash
./scripts/union_branch_build_and_test.sh
```

Fluxo resumido:
1. `main` atualizado
2. `Antigravity_Codex` resetado a partir de `origin/main`
3. merge de `origin/AntigravityIDE`
4. validacoes completas (backend/root/front/smokes)
5. push de `Antigravity_Codex` e PR `Antigravity_Codex -> main`

## Guard rail de branch
```bash
bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
```
