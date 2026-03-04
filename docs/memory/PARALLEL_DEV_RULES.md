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

## Protocolo triagente Mac VM EC2 (obrigatorio)
1. Toda solicitacao iniciada no `Agente Mac` deve ser executada e testada primeiro na `VM` (`vm-atualizacoes`).
2. Somente apos aprovacao da tarefa na VM, o Mac coordena aplicacao no `EC2` (`main`).
3. Se houver acao direta de operador na VM ou EC2, o Mac deve sincronizar estado completo no primeiro contato seguinte.
4. Cada agente publica apenas no proprio branch:
   - Mac -> `codex/AgenteMac`
   - VM -> `vm-atualizacoes`
   - EC2 -> `main`
5. Integracao final sem conflito exige consolidacao de status em `docs/memory/AGENT_SYNC_BOARD.md`.
