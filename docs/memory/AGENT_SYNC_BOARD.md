# Agent Sync Board

Quadro unico de sincronizacao entre os agentes `Mac`, `VM` e `EC2`.

## Topologia
- `Mac` (gestor/local): maquina principal.
- `VM` (dev principal): `ssh mrquentinha`.
- `EC2` (producao): `ssh mrquentinha_web`.

## Regras
1. Atualizar este quadro no inicio e no fim de cada ciclo de trabalho.
2. Toda divergencia entre VM e EC2 deve ter dono e prazo.
3. Toda decisao de impacto deve ser registrada tambem em `docs/memory/DECISIONS.md`.

## Snapshot consolidado
| Data/Hora | Agente | Ambiente | Branch | Ultimo commit | Smoke | Status | Riscos/Bloqueios | Proxima acao | Dono | Prazo |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-03 00:00 | Mac | Local | main | n/a | n/a | Ativo | Configurar fluxo triagente oficial | Publicar W26 e iniciar primeira reuniao | Mac | 2026-03-03 |

## Divergencias abertas
- Nenhuma registrada.
