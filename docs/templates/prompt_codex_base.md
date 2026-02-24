# Template — Prompt Base (estado atual)

## Contexto do projeto
- Leia `AGENTS.md` e siga as regras.
- Consulte: `docs/02-arquitetura.md`, `docs/03-modelo-de-dados.md`, `docs/memory/PROJECT_STATE.md`.

## Objetivo
<descreva exatamente o resultado esperado>

## Escopo
- Entra:
  - <itens que devem ser implementados>
- Nao entra:
  - <itens fora da tarefa>

## Arquivos relevantes
- <lista de arquivos/pastas para leitura/edicao>

## Definition of Done
- backend: `make lint` e `make test` ok (quando houver mudanca no backend)
- portal/client: `npm run lint` e `npm run build` ok (quando houver mudanca em frontend)
- scripts/smokes ajustados quando a tarefa exigir fluxo ponta a ponta
- documentacao atualizada (`CHANGELOG`, `DECISIONS`, e/ou runbooks)
- sem segredos em arquivos versionados

## Comandos de validacao
- <comandos exatos para reproduzir>

## Checklist antes de encerrar
- [ ] migracoes geradas/aplicadas quando necessario
- [ ] endpoints testados (curl/smoke)
- [ ] seed demo mantido funcional (se impactar dados/base)
- [ ] docs coerentes com o estado real

## Observacao
Se houver escolha tecnica, adotar a opcao mais simples do MVP e registrar em `docs/memory/DECISIONS.md`.
