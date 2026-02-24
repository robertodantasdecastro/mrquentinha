# Guia de Uso dos Workflows (Codex + Antigravity)

## Princípios
- Fonte de verdade: workflows `W10..W21`.
- Wrappers `00..06` existem para atalhos e onboarding.
- Nunca iniciar tarefa sem ler `AGENTS.md` e `GEMINI.md`.

## Política de branches
- Codex: `feature/etapa-4-orders` (ou `join/codex-ag` em integracao).
- Antigravity: `ag/<tipo>/<slug>`.
- Integracao: `join/codex-ag`.
- Guard rail obrigatorio:
  - `bash scripts/branch_guard.sh --agent codex --strict --codex-primary feature/etapa-4-orders --allow-codex-join`
  - `bash scripts/branch_guard.sh --agent antigravity --strict`
  - `bash scripts/branch_guard.sh --agent join --strict --codex-primary feature/etapa-4-orders`

## Fluxo recomendado (dia a dia)
1. `W10_iniciar_sessao`
2. `W02_feature_backend` ou `W03_feature_frontend`
3. `W16_auditoria_qualidade`
4. `W17_atualizar_documentacao_memoria`
5. `W21_sync_codex_antigravity`
6. `W12_salvar_checkpoint`

## Trabalho paralelo (Codex + Antigravity)
1. Antes de editar, ler `.agent/memory/IN_PROGRESS.md`.
2. Registrar lock humano no `IN_PROGRESS.md` (agente, branch, arquivos/areas).
3. Evitar editar os mesmos arquivos ao mesmo tempo.
4. Se houver intersecao, combinar ordem de entrega e usar `join/codex-ag` para integracao.
5. Fechar com `W21_sync_codex_antigravity` antes de checkpoint/PR.

## Quando usar W13, W14 e W15
- `W13`: bug localizado e reproducao clara.
- `W14`: causa raiz incerta, precisa de investigacao.
- `W15`: limpeza/refatoracao sem alterar comportamento.

## PR e release
- PR/merge: `W18_preparar_pr_merge`.
- Release/tag: `W19_release_tag` (sempre apos QA completo).

## Venv/NVM (obrigatorio)
- Testes no root: ativar venv do backend antes.
- NPM: carregar nvm e usar Node LTS antes de qualquer `npm run ...`.
