# Template - Workflow triagente para NovoProjeto

Use este template para replicar o modelo de governanca em outro repositorio.

## Passo 1 - Topologia de agentes
Defina no novo projeto:
- `Agente Mac` (gestor/local)
- `Agente VM` (dev principal)
- `Agente EC2` (producao)

## Passo 2 - Copiar workflows e memoria
Copiar para o novo repositorio:
- `.agent/workflows/W26_gestao_triagente_novoprojeto.md`
- `docs/memory/AGENT_SYNC_BOARD.md`
- `docs/memory/reunioes/README.md`
- `docs/memory/reunioes/TEMPLATE_REUNIAO.md`

## Passo 3 - Ajustar acessos
Atualizar comandos SSH no W26:
- DEV: `ssh <alias_vm>`
- PROD: `ssh <alias_ec2>`

## Passo 4 - Integrar no mapa de workflows
Atualizar:
- `.agent/workflows/WORKFLOW_MAP.md`
- `.agent/workflows/SESSION_COMMANDS.md`
- `.agent/workflows/USAGE_GUIDE.md`

## Passo 5 - Regra de ciclo
1. Snapshot dos 3 agentes.
2. Registro de divergencias com dono/prazo.
3. Ata de reuniao quando houver decisao.
4. Sync de memoria antes do checkpoint final.

## Criterio de sucesso
- Projeto com estado unico e rastreavel entre desenvolvimento e producao.
