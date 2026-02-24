# Regras de Desenvolvimento Paralelo (Codex + Antigravity)

## Objetivo
Permitir trabalho paralelo sem conflito de branch e com integracao rastreavel.

## Regras operacionais
1. Ler `AGENTS.md` e `/home/roberto/.gemini/GEMINI.md` no inicio da sessao.
2. Validar branch com `scripts/branch_guard.sh`.
3. Registrar lock humano em `.agent/memory/IN_PROGRESS.md` antes de editar.
4. Nao editar os mesmos arquivos em paralelo entre agentes.
5. Integracao entre linhas de trabalho sempre em `Antigravity_Codex`.
6. Encerrar ciclo com `W21_sync_codex_antigravity`.

## Papel de cada branch
- `main`: linha principal do Codex.
- `AntigravityIDE`: linha principal do Antigravity.
- `Antigravity_Codex`: branch neutro de uniao (merge/cherry-pick/PR), sem desenvolvimento continuo.

## Checklist anti-conflito
- [ ] `IN_PROGRESS.md` lido
- [ ] `IN_PROGRESS.md` atualizado
- [ ] branch validada por `branch_guard`
- [ ] sem intersecao de arquivos em edicao
- [ ] integracao feita em `Antigravity_Codex`
- [ ] `W21` executado antes do checkpoint final
