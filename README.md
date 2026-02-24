# Mr Quentinha — Documentação de Desenvolvimento (MVP)

Este repositório contém **toda a documentação inicial** para começar o desenvolvimento do aplicativo **Mr Quentinha** (marmitas) e da plataforma web de gestão, com **backend único** (API) atendendo:
- **App mobile** (Android/iOS) para clientes fazerem pedidos
- **Web** (gestão interna) para cardápios, estoque, compras e financeiro

> Objetivo: permitir que você use o **Codex** como copiloto/agente de engenharia, com regras e contexto persistentes, mantendo o projeto **escalonável, seguro e evolutivo (POO)** desde o primeiro dia.

## Estrutura (alto nível)

- `AGENTS.md` → instruções do projeto para o Codex (lidas automaticamente).
- `docs/` → documentação detalhada por tema e por fase.
- `docs/templates/` → prompts prontos para usar no Codex (scaffold, feature, bugfix, etc.).
- `docs/adr/` → decisões de arquitetura (Architecture Decision Records).
- `docs/checklists/` → checklists (Definition of Done, revisão, release).
- `workspaces/` → pastas sugeridas (backend, web, mobile), inicialmente vazias.

## Como usar esta documentação

1. Leia `docs/00-visao-geral.md` e `docs/01-escopo-mvp.md`
2. Siga o setup local em `docs/08-setup-vm-linux-sem-docker.md`
3. Configure o Codex com `AGENTS.md` + `docs/07-workflow-codex.md`
4. Execute o plano do MVP em `docs/10-plano-mvp-cronograma.md`

## Observação importante sobre distribuição iOS
Distribuir um app iOS **fora da App Store** tem restrições e normalmente exige **TestFlight** ou programas específicos (Enterprise/MDM). No MVP, recomenda-se:
- Priorizar Android (APK) para pilotos
- Planejar iOS via TestFlight quando for a hora

## Próximos passos (rápidos)
- **Passo 1:** criar scaffold do backend + migrações iniciais (ver `docs/templates/prompt_codex_scaffold_backend.md`)
- **Passo 2:** criar scaffold do web admin (ver `docs/templates/prompt_codex_scaffold_web.md`)
- **Passo 3:** criar scaffold do mobile (ver `docs/templates/prompt_codex_scaffold_mobile.md`)


## Execucao de testes (root e backend)
No root do repositorio (`~/mrquentinha`):

- `make test`
- `pytest`

Os comandos acima usam o backend em `workspaces/backend`.

Direto no backend:

- `cd workspaces/backend && make test`
- `cd workspaces/backend && make lint`
- `cd workspaces/backend && make format`

## Subir stack de desenvolvimento (backend + portal)
Comandos no root do repositorio (`~/mrquentinha`):

1. Backend (Django + migrate + runserver 8000):
```bash
./scripts/start_backend_dev.sh
```

2. Portal (Next.js dev server 3000):
```bash
./scripts/start_portal_dev.sh
```

Obs:
- Use dois terminais separados (um para backend e outro para portal).
- Encerramento com `Ctrl+C` e tratado de forma limpa pelos scripts.

3. Smoke test completo do stack (sobe backend + portal, valida endpoints e encerra):
```bash
./scripts/smoke_stack_dev.sh
```
