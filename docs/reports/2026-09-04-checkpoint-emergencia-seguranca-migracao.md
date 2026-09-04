# Checkpoint emergencial de seguranca e migracao — 04/09/2026

## Identificacao e escopo
- Owner documental: Tereza.
- Gestor: Ze (`ZERO_WRITE` durante este fechamento).
- UTC de referencia documental: `2026-09-04T14:24:55Z`.
- Checkout canonico: `/home/ubuntu/mrquentinha`.
- Este registro encerra documentalmente os hotfixes de seguranca, o backup preventivo, o preflight de migracao e o bloqueio da candidata P1-04A.
- Nenhum codigo, banco, servico, env, backup, DNS/Cloudflare, provider ou runtime `cereus_web` foi alterado por este fechamento.

## Estado canonico publicado
- `HEAD/main/origin/main/remote main`: `985c1cb8bc1c545baa8cb81fa0ca7ebf9d2ea296`.
- Worktree canonica: limpa; stage vazio.
- Health tecnico final: API health, `www`, `app` e `admin` responderam HTTP 200.
- Pagamentos: provider exclusivamente `mock`.
- DNS/Cloudflare: intocados.
- Runtime `cereus_web`: intocado.

Gates:
- `PUBLISHED_CURRENT=PASS` para o SHA canonico acima.
- Revisoes independentes e testes tecnicos dos commits publicados: `PASS`.
- P0 pagamento `LIVE_E2E_SECURITY=NOT_RUN`: nao houve prova externa role-specific segura sem dados reais.
- P0 Portal `LIVE_E2E_SECURITY_PARTIAL=PASS`: provas negativas live/in-process foram sanitizadas e sem side effect.
- `HUMAN_ACCEPTED=NOT_RUN`.

## Backup preventivo e restore isolado
- Backup: `/var/backups/mrquentinha/20260904T105304Z`.
- O backup local esta no mesmo volume da origem; a copia/snapshot off-host permaneceu bloqueada e segue como risco residual.
- Dump PostgreSQL custom, arquivos operacionais permitidos, inventario e verificacao de integridade: `PASS`.
- Catalogo do dump via `pg_restore --list`: `PASS`.
- Restore isolado preservado: `mrquentinha_restore_verify_20260904_105304`.
- Comparacao agregada: 60 tabelas e 3762 linhas; `RESTORE_ISOLATED=PASS`.
- Nenhum hash, valor secreto ou dado pessoal e reproduzido neste relatorio.
- Snapshot EBS/off-host: `BLOCKED_AUTH`; AWS CLI/autoridade de control-plane nao estavam disponiveis.
- O backup e o banco restaurado permanecem preservados; cleanup/drop nao foi autorizado.

## Releases emergenciais publicadas

### P0 — autorizacao de pagamento
- Commit: `4a497c6f9937da8ba1b130ffd79675260eacde29`.
- Publicacao: `PASS`.
- Testes tecnicos e prova negativa sem pedido/pagamento real: `PASS`.

### P0 — Portal RBAC/SQL
- Commits: `bb54b812fec06003931e03c8918d311fe0c17727` e `a90d52be63db6425eede8ddecd67901b6a61ca4b`.
- Publicacao: `PASS`.
- Provas negativas sanitizadas: operacoes SQL criticas e destroy de configuracao negados, sem backend tecnico real e sem side effect; `PASS`.

### P1 — origem canonica e producao fail-closed
- Commits: `0aeedc9af96480702f5e68b5ce28b3b91c0223f6` e `985c1cb8bc1c545baa8cb81fa0ca7ebf9d2ea296`.
- Publicacao: `PASS`.
- Settings de producao, validador Fernet e resolucao de origem hostil para origem HTTPS oficial: `PASS`, sem envio de e-mail e sem exposicao de token.

As revisoes independentes exigidas para esses batons foram aceitas tecnicamente. Isso nao substitui `HUMAN_ACCEPTED`, que permanece `NOT_RUN`.

## Ativacao do backend e licao operacional
- O primeiro deploy usou restart do backend.
- A dependencia `systemd Requires` propagou a operacao aos frontends e houve aproximadamente 25 segundos de HTTP 502 durante o aquecimento.
- Depois da recuperacao, todos os endpoints ficaram saudaveis.
- Os deploys posteriores confirmaram master Gunicorn e usaram somente HUP.
- Nas ativacoes por HUP, o master permaneceu, houve troca de worker, os PIDs dos frontends foram invariantes e nao surgiram novos 5xx/traceback.
- Decisao: para codigo Python sem migration/build, manter HUP sob baton explicito ate redesenhar e testar as units. Redesenho de `Requires`, ordenacao e rollback e uma frente separada.

## P1-04A — candidata protegida, nao promovida
- Worktree: `/home/ubuntu/mrquentinha-sec-p1-04a`.
- Branch: `codex/emergency-webhook-guard-20260904`.
- Estado: 7 arquivos modificados, stage vazio, sem commit e sem push.
- Arquivos modificados:
  - `workspaces/backend/src/apps/orders/services.py`;
  - `workspaces/backend/src/apps/orders/throttling.py`;
  - `workspaces/backend/src/apps/orders/views.py`;
  - `workspaces/backend/src/config/settings/base.py`;
  - `workspaces/backend/src/config/settings/prod.py`;
  - `workspaces/backend/tests/test_orders_api.py`;
  - `workspaces/backend/tests/test_orders_services.py`.
- Resultado: `BLOCKED_HARNESS`, com 22 testes `PASS` e 1 `FAIL`.
- Causa exata: `django_assert_num_queries(0)` contou `SAVEPOINT`, `ROLLBACK TO SAVEPOINT` e `RELEASE SAVEPOINT` criados pelo harness transacional.
- A evidencia nao mostrou `SELECT`, `INSERT`, `UPDATE` ou `DELETE`.
- Interpretacao: a falha e do contrato do harness atual, mas a candidata nao pode ser declarada segura, publicada ou aceita antes do gate completo.
- Gate nominal `NOT_STARTED`: ajustar a assercao para distinguir comandos transacionais de SQL de dados, executar suite completa, obter revisao independente e decidir deploy em baton proprio.

## Pendencias de seguranca e produto
- P1-04B, limites de upload/OCR: `NOT_STARTED`.
- P1-05, LGPD/minimizacao/retencao de auditoria: `NOT_STARTED`.
- Segredos do Portal externalizados e write-only: `NOT_STARTED`.
- Providers reais e webhooks reais: `BLOCKED`.
- Mobile, OAuth, CI e lacunas de UX do MVP: permanecem abertas, sem promocao neste checkpoint.
- Item 3/Tarcila: `SPEC/NOT_STARTED`; somente apos migracao/nova instancia, com Tarcila, Lina e Eliane. `HUMAN_ACCEPTED` continua um gate separado.

## `cereus_web` e migracao de capacidade futura
- Evidencia read-only: filesystem raiz com 14 GiB totais e 3.0 GiB livres.
- Regra operacional: `<=5 GiB` implica `STOP` no ponto atomico seguro.
- Compatibilidade observada: sem Node, sem swap e com aplicacoes compartilhadas.
- Nenhuma escrita ou preparacao foi feita no host.
- Gate futuro `NOT_STARTED`: criar EBS gp3 separado de 60 GiB e migrar transparentemente `/var`, `/home` e `/opt`, incluindo PostgreSQL e releases.
- Precondicoes: owner exclusivo, autorizacao AWS control-plane, backup e snapshot, mapa de dependencias, espaco/inodes, plano de mount/fstab/binds/ordem, verificacao de boot/servicos e rollback testavel.
- DNS/cutover e posterior, separado e somente mediante instrucao explicita de Roberto.

## Limites preservados
- Nenhum restart/HUP neste fechamento documental.
- Nenhuma migration, escrita/restore/drop de banco ou cleanup.
- Nenhuma alteracao em env, segredos, certificados, units, Nginx, firewall, DNS, Cloudflare ou providers.
- Nenhuma edicao, stage, commit, push ou limpeza da worktree P1-04A.
- Nenhuma escrita no checkout local sujo do Mac.

## Estado de pausa e retomada
- Todos os agentes: `ZERO_WRITE/STANDBY`.
- Locks tecnicos: livres no fechamento.
- Processos de escrita/deploy/backup concorrentes: nenhum observado no fechamento.
- `RESUME_REQUIRES_NEW_EXPLICIT_MANAGER_REQUEST=YES`.
- Nao ha proximo baton aberto por este checkpoint.
