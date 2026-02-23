# Workflow do Codex (configuração e uso no dia a dia)

## Onde o Codex entra no processo
Você vai usar o Codex para:
- gerar scaffolds
- implementar features pequenas com testes
- revisar código
- refatorar
- escrever documentação e ADRs

## Como manter “memória” do projeto
O Codex funciona melhor quando existe um “núcleo” de contexto estável:
- `AGENTS.md` (regras do projeto)
- `docs/02-arquitetura.md` e `docs/03-modelo-de-dados.md`
- `docs/memory/DECISIONS.md` (decisões vivas)
- `docs/memory/CHANGELOG.md` (o que mudou por sprint)

**Regra**: a cada mudança importante, atualizar `DECISIONS.md` e/ou criar um ADR.

## Estratégia de prompts (essencial)
Sempre inclua:
1. contexto (arquivos e objetivo)
2. definição de pronto (DoD)
3. restrições (sem Docker, Postgres, etc.)
4. como validar (comandos de teste)

Veja os templates em `docs/templates/`.

## Controle de escopo
- Um prompt = uma tarefa pequena.
- Evite “implemente o sistema inteiro”.
- Preferir: “implemente o CRUD de ingredientes + testes + endpoints”.

## Review checklist (quando o Codex entregar)
- Rodou local?
- Testes passam?
- Migrações ok?
- Sem segredos?
- Documentação atualizada?

## Observação oficial do Codex
- O Codex lê `AGENTS.md` antes de trabalhar e recomenda definir “Definition of Done” e contexto explícito. 


## Regra extra (UI/Frontend)
Sempre que gerar telas web/mobile:
- importar/aplicar tokens de `assets/brand/tokens.css` e `assets/brand/tokens.json`
- garantir light/dark mode
- utilizar a logo oficial em `assets/brand/`
