<!-- REPO_HEADER_START -->
# GEMINI (Espelho Versionado)

Este arquivo espelha `~/.gemini/GEMINI.md`; sincronize com:

```bash
bash scripts/sync_gemini_global.sh
```
<!-- REPO_HEADER_END -->

# GEMINI - Global Antigravity

## Politica de Branches (Anti-Conflito)
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`

### Regras canonicas
- Codex trabalha somente em:
  - `main`
  - `main/etapa-N-TituloEtapa`
- Antigravity trabalha somente em:
  - `AntigravityIDE`
  - `AntigravityIDE/etapa-N-TituloEtapa`
- `Antigravity_Codex` e branch neutro de uniao para merge/cherry-pick/PR.
  - Nao e workspace de trabalho continuo da IDE.
- Nunca trabalhar na branch principal do outro agente.

## Regra de branches por etapa
- Codex:
  - iniciar etapa: `git checkout -b main/etapa-N-TituloEtapa main`
  - concluir etapa: consolidar `main/etapa-*` em `main` (merge/ff).
- Antigravity:
  - iniciar etapa: `git checkout -b AntigravityIDE/etapa-N-TituloEtapa AntigravityIDE`
  - concluir etapa: consolidar `AntigravityIDE/etapa-*` em `AntigravityIDE` (merge/ff).
- Uniao:
  - criar/atualizar `Antigravity_Codex` a partir de `origin/main`.
  - trazer mudancas de `origin/AntigravityIDE`.
  - abrir PR `Antigravity_Codex -> main` (merge final somente Codex).

## Guard rail obrigatorio
Sempre validar branch antes de commit/push:

```bash
bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
```

## Uniao oficial com validacao completa
```bash
./scripts/union_branch_build_and_test.sh
```
Use `--dry-run` para simular sem executar.

## Seguranca
- Nao salvar segredos em git.
- `.env` real e credenciais ficam fora de versionamento.
