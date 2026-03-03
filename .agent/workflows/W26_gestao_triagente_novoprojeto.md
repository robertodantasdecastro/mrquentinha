---
id: W26
title: Gestao triagente (NovoProjeto)
description: Orquestrar os agentes Mac, VM e EC2 com registro de reunioes, sincronizacao de estado e trilha de decisoes.
inputs:
  - objetivo_ciclo
  - escopo (backend|frontend|infra|full)
  - registrar_reuniao (sim|nao)
outputs:
  - snapshot_triagente
  - plano_unificado
  - ata_publicada (quando registrar_reuniao=sim)
commands:
  - sed -n '1,220p' AGENTS.md
  - bash scripts/gemini_check.sh
  - bash scripts/branch_guard.sh --agent codex --strict --codex-primary main --antigravity-branch AntigravityIDE --union-branch Antigravity_Codex
  - git branch --show-current && git status -sb
  - ssh mrquentinha 'cd ~/mrquentinha && git branch --show-current && git status -sb'
  - ssh mrquentinha 'cd ~/mrquentinha && bash scripts/smoke_stack_dev.sh'
  - ssh mrquentinha_web 'cd ~/mrquentinha && git branch --show-current && git status -sb'
  - ssh mrquentinha_web 'cd ~/mrquentinha && bash scripts/smoke_stack_dev.sh'
  - atualizar docs/memory/AGENT_SYNC_BOARD.md
  - atualizar docs/memory/PROJECT_STATE.md
  - criar/atualizar docs/memory/reunioes/YYYY-MM-DD-<slug>.md
  - bash scripts/sync_memory.sh --check
quality_gate:
  - estado dos 3 agentes registrado
  - riscos e bloqueios com dono/prazo
  - sincronizacao de memoria sem pendencias
memory_updates:
  - docs/memory/AGENT_SYNC_BOARD.md
  - docs/memory/PROJECT_STATE.md
  - docs/memory/reunioes/YYYY-MM-DD-<slug>.md (quando houver reuniao)
---

# W26 - Gestao Triagente (NovoProjeto)

## Topologia oficial
- `Agente Mac` (gestor): maquina principal local (este Codex).
- `Agente VM` (dev principal): acesso por `ssh mrquentinha`.
- `Agente EC2` (producao): acesso por `ssh mrquentinha_web`.

## Objetivo
Manter um unico estado confiavel da aplicacao entre desenvolvimento e producao, com governanca explicita de:
- status tecnico por ambiente;
- decisoes e riscos;
- plano de execucao por responsavel;
- atas de reuniao rastreaveis.

## Responsabilidades por agente
- `Mac (gestor)`:
  - coordenar prioridade, escopo e sequencia de entrega;
  - consolidar estado em memoria viva;
  - abrir/fechar reunioes e cobrar acoes.
- `VM (dev principal)`:
  - implementar features e correcao no ambiente de desenvolvimento;
  - executar qualidade/smoke no ciclo tecnico.
- `EC2 (producao)`:
  - validar impacto operacional e disponibilidade;
  - executar smokes e checks de operacao em producao.

## Artefatos obrigatorios
1. `docs/memory/AGENT_SYNC_BOARD.md` atualizado em todo ciclo.
2. Ata quando `registrar_reuniao=sim` em `docs/memory/reunioes/`.
3. Atualizacao de `PROJECT_STATE.md` com diferencas relevantes entre VM e EC2.

## Cadencia recomendada
1. Inicio do dia: snapshot rapido dos 3 agentes.
2. Meio do dia: consolidacao de riscos e desvios.
3. Fechamento: convergencia de estado + proximo passo unico.

## Roteiro de execucao
1. Rodar preflight local (`AGENTS`, `gemini_check`, `branch_guard`).
2. Capturar estado `Mac/VM/EC2` (branch, status git, smoke).
3. Registrar quadro consolidado em `AGENT_SYNC_BOARD.md`.
4. Se houver reuniao, gerar ata com decisoes e plano de acao.
5. Atualizar `PROJECT_STATE.md` com divergencias e proximos passos.
6. Finalizar com `bash scripts/sync_memory.sh --check`.

## Criterio de saida
- Existe uma versao unica do estado do projeto, com dono por acao, prazo e ambiente alvo (VM ou EC2).
