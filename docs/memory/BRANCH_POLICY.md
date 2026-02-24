# Branch Policy (Codex x Antigravity x Join)

Atualizado em: 24/02/2026.

## Variavel de referencia
- `BRANCH_CODEX_PRIMARY=feature/etapa-4-orders`

## Regras
1. Codex trabalha somente em `BRANCH_CODEX_PRIMARY`.
2. Antigravity trabalha somente em branches `ag/<tipo>/<slug>`.
3. Integracao entre agentes ocorre em `join/codex-ag`.
4. Nao alterar historico das branches originais durante integracao.

## Guard rail de branch
Script oficial:

```bash
bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders
bash scripts/branch_guard.sh --agent antigravity --strict
bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders
```

## Fluxo recomendado
### Codex
```bash
git checkout feature/etapa-4-orders
bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders
```

### Antigravity
```bash
git checkout -b ag/chore/smoke-rbac
bash scripts/branch_guard.sh --agent antigravity --strict
```

### Join (integracao)
```bash
git checkout -B join/codex-ag feature/etapa-4-orders
bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders

git merge --no-ff ag/chore/smoke-rbac
# resolver conflitos, rodar quality gate
```

## Observacao
- Opcao futura (nao implementada): automatizar login JWT no smoke para fluxos privados.
