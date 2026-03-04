---
id: W27
title: Sync Mac VM EC2
description: Protocolo oficial de coordenacao entre Agente Mac, Agente VM e Agente EC2.
inputs:
  - origem_solicitacao (mac|vm|ec2)
  - objetivo
  - aprovacao_ec2 (sim|nao)
outputs:
  - relatorio_sync_triagente
commands:
  - git branch --show-current && git status -sb
  - ssh mrquentinha 'cd ~/mrquentinha && git branch --show-current && git status -sb'
  - ssh mrquentinha_web 'cd ~/mrquentinha && git branch --show-current && git status -sb'
  - ssh mrquentinha 'cd ~/mrquentinha && bash scripts/smoke_stack_dev.sh'
  - ssh mrquentinha_web 'cd ~/mrquentinha && bash scripts/smoke_stack_dev.sh'
  - atualizar docs/memory/AGENT_SYNC_BOARD.md
  - atualizar docs/memory/PARALLEL_DEV_RULES.md
quality_gate:
  - toda solicitacao iniciada no Mac passa por execucao e teste na VM antes de EC2
  - EC2 recebe apenas mudanca validada e aprovada
  - branches preservadas por agente sem conflito
memory_updates:
  - docs/memory/AGENT_SYNC_BOARD.md
  - docs/memory/PARALLEL_DEV_RULES.md
---

# W27 - Sync Mac VM EC2

## Objetivo
Garantir um ciclo unico de coordenacao entre os tres agentes, com ordem fixa de execucao e publicacao sem conflito.

## Branch oficial por agente
- `Agente Mac` -> `codex/AgenteMac`
- `Agente VM (Dev)` -> `vm-atualizacoes`
- `Agente EC2 (Producao)` -> `main`

## Regra de execucao (obrigatoria)
1. Se a solicitacao vier do `Agente Mac`, toda implementacao/correcao deve ser executada e testada primeiro na VM.
2. So apos teste e aprovacao da tarefa na VM, o Mac coordena a aplicacao no EC2.
3. Nenhuma publicacao no `main` sem etapa previa na VM (exceto hotfix emergencial aprovado explicitamente pelo operador).

## Regra de sincronizacao quando houver acoes locais em VM/EC2
1. Se operador atuar direto na VM ou EC2, o `Agente Mac` deve sincronizar no primeiro contato seguinte.
2. Sincronizar significa:
   - comparar branch/commit entre os tres ambientes;
   - registrar divergencias no `AGENT_SYNC_BOARD`;
   - alinhar memoria e proximo passo unico;
   - evitar conflito por branch cruzada.

## Regra de git/publicacao
1. Cada agente publica apenas no proprio branch.
2. Proibido push cruzado de branch entre agentes.
3. Integracao final em producao ocorre somente no `main` da EC2, coordenada pelo Mac.

## Checklist do ciclo
1. Confirmar branch atual nos 3 ambientes.
2. Executar implementacao e testes na VM.
3. Registrar resultado e aprovacao no board de sincronizacao.
4. Aplicar no EC2 apenas apos aprovacao.
5. Confirmar smokes pos-aplicacao.
6. Salvar memoria e finalizar com status + proximo passo.

## Criterio de saida
- Estado coerente entre Mac, VM e EC2, com rastreabilidade de branch, testes e decisao de publicacao.
