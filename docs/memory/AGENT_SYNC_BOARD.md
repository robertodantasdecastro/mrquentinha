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
| 2026-03-06 12:55 | Mac | Local | codex/AgenteMac | 8b08e6e | checklist git OK | Em sincronizacao | Nenhum | Propagar endurecimento de `.gitignore` para VM/EC2 e concluir limpeza operacional | Mac | 2026-03-06 |
| 2026-03-06 12:55 | VM | Desenvolvimento | vm-atualizacoes | 2ff1efb | checklist git OK | Em sincronizacao | Nenhum | Receber commit de limpeza (`btop.png`) e validar status limpo | VM | 2026-03-06 |
| 2026-03-06 12:55 | EC2 | Producao | main | 9b268fd | API health OK / admin HTTP 200 | Em sincronizacao | `btop.png` local (nao versionado) | Remover arquivo local e sincronizar regra de ignore no `main` | EC2 | 2026-03-06 |
| 2026-03-05 09:40 | Mac | Local (gestao) | codex/AgenteMac | b8acf4b | validacao documental OK (sem acesso SSH aos hosts) | Parcialmente sincronizado | Hostnames `mrquentinha` e `mrquentinha_web` indisponiveis neste ambiente de coordenacao | Aguardar retorno do Agente Mac para executar checklist remoto na VM e confirmar smokes | Mac | 2026-03-05 |
| 2026-03-05 09:40 | VM | Desenvolvimento | vm-atualizacoes | 8a4e81b (informado) | pendente de comprovacao remota neste ambiente | Aguardando confirmacao operacional | Sem resolucao DNS/SSH para `mrquentinha` neste ambiente | Executar `git status` + smoke stack na VM no proximo contato do Mac | VM | proximo ciclo |
| 2026-03-05 09:40 | EC2 | Producao | main | abda7d1 (local atual) | pendente de comprovacao remota neste ambiente | Aguardando confirmacao operacional | Sem resolucao DNS/SSH para `mrquentinha_web` neste ambiente | Confirmar smokes HTTP 200 em producao apos checklist VM | EC2 | proximo ciclo |
| 2026-03-04 12:25 | Mac | Local | codex/AgenteMac | 1dead57 | build+lint admin OK | Sincronizado | Nenhum | Registrar memoria final do ciclo e manter coordenacao triagente | Mac | 2026-03-04 |
| 2026-03-04 12:25 | VM | Desenvolvimento | vm-atualizacoes | c90b2ad | build+lint admin OK | Sincronizado | Nenhum | Manter VM como primeira etapa de execucao/teste | VM | continuo |
| 2026-03-04 12:25 | EC2 | Producao | main | 14abf63 | health API + web/app/admin HTTP 200 | Sincronizado | `btop.png` untracked local | Seguir publicacao controlada apos aprovacao VM | EC2 | continuo |
| 2026-03-04 12:00 | Mac | Coordenacao | codex/AgenteMac | em andamento | n/a | Ativo | Formalizar protocolo triagente continuo | Publicar W27 e propagar regras em VM/EC2 | Mac | 2026-03-04 |
| 2026-03-03 00:00 | Mac | Local | main | n/a | n/a | Ativo | Configurar fluxo triagente oficial | Publicar W26 e iniciar primeira reuniao | Mac | 2026-03-03 |

## Divergencias abertas
- Pendencia operacional de `btop.png` local na EC2 em tratamento no ciclo 06/03/2026.
- Snapshot anterior (04/03) registrava commits `1dead57`/`c90b2ad`/`14abf63`; estado esperado atualizou para `b8acf4b`/`8a4e81b`/`abda7d1` e foi registrado como baseline do ciclo 05/03.
- Validacao remota de VM/EC2 bloqueada neste ambiente por falha de resolucao DNS dos aliases SSH (`mrquentinha`, `mrquentinha_web`).
