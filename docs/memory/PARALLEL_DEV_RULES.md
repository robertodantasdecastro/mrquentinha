# Regras de Desenvolvimento Paralelo (Codex + Antigravity)

## Objetivo
Permitir trabalho paralelo sem conflito de branch, sem sobrescrita de arquivos e com sincronizacao obrigatoria.

## Regras operacionais
1. Ler `AGENTS.md` e `GEMINI.md` no inicio da sessao.
2. Validar branch com `scripts/branch_guard.sh`.
3. Registrar lock humano em `.agent/memory/IN_PROGRESS.md` antes de editar.
4. Nao editar os mesmos arquivos em paralelo entre agentes.
5. Se houver dependencia cruzada, integrar em `join/codex-ag`.
6. Encerrar ciclo com `W21_sync_codex_antigravity`.

## Quando usar cada agente
- Codex:
  - consolidacao da branch principal (`feature/etapa-4-orders`)
  - integracao final em `join/codex-ag`
- Antigravity:
  - execucao paralela em `ag/<tipo>/<slug>`
  - entrega via PR para integracao

## Checklist rapido anti-conflito
- [ ] `IN_PROGRESS.md` lido
- [ ] `IN_PROGRESS.md` atualizado
- [ ] branch validada por `branch_guard`
- [ ] sem intersecao de arquivos em edicao
- [ ] `W21` executado antes de commit final
