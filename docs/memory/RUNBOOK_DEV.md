# Runbook DEV (stack completo)

## 1) Subir stack local
No root (`~/mrquentinha`), em terminais separados:

```bash
./scripts/start_backend_dev.sh
./scripts/start_portal_dev.sh
./scripts/start_client_dev.sh
```

Acessos:
- API: `http://127.0.0.1:8000`
- Portal: `http://127.0.0.1:3000`
- Web Cliente: `http://127.0.0.1:3001`

## 2) Sessao e paralelo (Codex + Antigravity)
1. Ler `AGENTS.md` e `/home/roberto/.gemini/GEMINI.md`.
2. Validar regra global:

```bash
bash scripts/gemini_check.sh
```

3. Ler `.agent/memory/IN_PROGRESS.md`.
4. Validar branch:

```bash
bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent antigravity --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
bash scripts/branch_guard.sh --agent union --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
```

5. Atualizar lock humano (`IN_PROGRESS.md`) antes de editar.

## 3) GEMINI global-only
- Fonte unica operacional: `/home/roberto/.gemini/GEMINI.md`.
- O repositorio nao e fonte de verdade para GEMINI.

Editar/validar:

```bash
nano ~/.gemini/GEMINI.md
bash scripts/gemini_check.sh
```

Snapshot opcional para documentacao:

```bash
cp ~/.gemini/GEMINI.md docs/memory/GEMINI_SNAPSHOT.md
bash scripts/diff_gemini.sh
```

## 4) Smoke
Validacao ponta a ponta:

```bash
./scripts/smoke_stack_dev.sh
```

Validacao rapida do client:

```bash
./scripts/smoke_client_dev.sh
```

## 5) Quality gate padronizado
```bash
bash scripts/quality_gate_all.sh
```

## 6) Sync obrigatorio antes de commit final
```bash
bash scripts/gemini_check.sh
bash scripts/sync_memory.sh --check
```

## 7) Uniao oficial (main + AntigravityIDE)
```bash
./scripts/union_branch_build_and_test.sh
```

Simulacao sem executar:
```bash
./scripts/union_branch_build_and_test.sh --dry-run
```

## 8) Recovery read-only (W25)
Quando houver travamento/divergencia e necessario diagnostico sem alterar nada:
1. Executar workflow `W25_recovery_readonly`.
2. Registrar saida em `docs/memory/RECOVERY_TEMPLATE.md`.
3. Atualizar este runbook com novos troubleshooting recorrentes.

## 9) Troubleshooting
- `DisallowedHost`:
  - revisar `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`.
- CORS:
  - revisar `CORS_ALLOWED_ORIGINS`.
- Next lock:
  - remover apenas `workspaces/web/client/.next/dev/lock` apos encerrar processo.
- Porta ocupada:
  - `ss -ltnp | grep -E ':8000|:3000|:3001'`

## 10) Quality gate sem conflito com tmux live
Quando houver sessoes live (`backend_live`, `portal_live`, `client_live`) ativas, o `quality_gate_all.sh` pode falhar em smoke por porta ocupada.

Fluxo recomendado:

```bash
# 1) pausar servicos live
tmux send-keys -t backend_live C-c
tmux send-keys -t portal_live C-c
tmux send-keys -t client_live C-c

# 2) validar portas livres
ss -ltnp | egrep ':8000|:3000|:3001' || true

# 3) executar gate completo
bash scripts/quality_gate_all.sh

# 4) religar servicos oficiais
tmux send-keys -t backend_live 'cd ~/mrquentinha && ./scripts/start_backend_dev.sh' C-m
tmux send-keys -t portal_live 'cd ~/mrquentinha && ./scripts/start_portal_dev.sh' C-m
tmux send-keys -t client_live 'cd ~/mrquentinha && ./scripts/start_client_dev.sh' C-m
```

## 11) Recovery rapido de travamento de conexao/SSH
1. Reconectar na VM e entrar no repo:
```bash
ssh mrquentinha
cd ~/mrquentinha
```
2. Validar estado minimo:
```bash
bash scripts/gemini_check.sh
git branch --show-current
git status -sb
bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
```
3. Reanexar tmux do agente:
```bash
tmux attach -d -t codex
```
4. Conferir sessoes de servico:
```bash
tmux ls
```

## 12) Locks Next.js + nvm/venv (recuperacao)

### Lock orfao do Next
Remover somente quando nao houver `next dev` ativo para o app:
```bash
pgrep -f 'workspaces/web/client/node_modules/.bin/next dev' || true
rm -f workspaces/web/client/.next/dev/lock
```

### Recarregar Python venv (backend)
```bash
cd ~/mrquentinha/workspaces/backend
source .venv/bin/activate
```

### Recarregar Node LTS (frontend)
```bash
source ~/.nvm/nvm.sh
nvm use --lts
```
