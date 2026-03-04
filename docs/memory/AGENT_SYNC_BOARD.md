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
4. Solicitacao do Agente Mac sempre executa/testa primeiro na VM antes de seguir para EC2.
5. Acao direta de operador em VM/EC2 exige sincronizacao obrigatoria pelo Mac no proximo contato.
6. Publicacao por branch fixa:
   - Mac -> `codex/AgenteMac`
   - VM -> `vm-atualizacoes`
   - EC2 -> `main`

## Snapshot consolidado
| Data/Hora | Agente | Ambiente | Branch | Ultimo commit | Smoke | Status | Riscos/Bloqueios | Proxima acao | Dono | Prazo |
|---|---|---|---|---|---|---|---|---|---|---|
| 2026-03-04 12:00 | Mac | Coordenacao | codex/AgenteMac | em andamento | n/a | Ativo | Formalizar protocolo triagente continuo | Publicar W27 e propagar regras em VM/EC2 | Mac | 2026-03-04 |
| 2026-03-03 00:00 | Mac | Local | main | n/a | n/a | Ativo | Configurar fluxo triagente oficial | Publicar W26 e iniciar primeira reuniao | Mac | 2026-03-03 |

## Divergencias abertas
- Nenhuma registrada.
