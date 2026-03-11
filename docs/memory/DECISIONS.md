# Decisoes vivas do projeto

Use este arquivo para registrar decisoes "em andamento" (menos formais).
Quando uma decisao for definitiva e afetar arquitetura, crie um ADR em `docs/adr/`.

## Padroes definidos
- Backend: Django + DRF
- DB: PostgreSQL
- Sem Docker no MVP
- Mobile: React Native
- Web Gestao: React/Next

## Itens para decidir (aberto)
- Homologacao final dos gateways de pagamento (Mercado Pago, Efi e Asaas) com credenciais reais e assinatura de webhook por provider
- OCR (servico externo vs interno)
- Distribuicao iOS (TestFlight/Enterprise)

## Marca
- Nome: Mr Quentinha
- Dominio: www.mrquentinha.com.br
- Cor primaria: #FF6A00
- Assets: assets/brand/

## Pendencias tecnicas (catalogo)
- RBAC do `catalog` ainda esta em modo MVP com `AllowAny` nas views.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Cozinha CRUD, Financeiro leitura e Cliente leitura de cardapio).

## Pendencias tecnicas (inventory/procurement)
- RBAC de `inventory` e `procurement` ainda esta temporario com `AllowAny` no MVP.
- Proxima etapa deve substituir por permissoes por perfil (Admin/Compras/Estoque CRUD, Cozinha criacao de solicitacao e leitura, Financeiro leitura).

## 03/03/2026 - Governanca triagente (Mac + VM + EC2) para NovoProjeto
- Decisao:
  - institucionalizar o modelo de 3 agentes com papeis fixos:
    - `Mac` como gestor de projeto e consolidacao de memoria;
    - `VM` como ambiente principal de desenvolvimento;
    - `EC2` como ambiente de producao e validacao operacional.
  - criar workflow dedicado `W26_gestao_triagente_novoprojeto` para coordenar snapshot de estado, registro de reunioes e sincronizacao de memoria.
  - adotar artefatos obrigatorios de governanca:
    - `docs/memory/AGENT_SYNC_BOARD.md` (quadro consolidado dos 3 agentes);
    - `docs/memory/reunioes/*.md` (atas com decisoes, acoes, dono e prazo).
- Consequencia:
  - toda evolucao passa a ter rastreabilidade cruzada entre local, VM e producao.
  - reducao de perda de contexto entre agentes e maior previsibilidade de entrega para novos projetos que reutilizem a arquitetura.

## 03/03/2026 - DB Ops via Web Admin com SSH e dumps versionados
- Decisao:
  - centralizar operacoes de banco de producao no Web Admin com pre-requisito de SSH configurado.
  - adotar dump PostgreSQL custom (`pg_dump -Fc`) como formato padrao para backup e replicacao.
  - complementar com `django-dbbackup` para operacao orientada a Django (`dbbackup/listbackups/dbrestore`) quando a equipe precisar fluxo framework-first.
  - exigir confirmacao explicita (`RESTAURAR`) para restore remoto.
  - expor tres modos operacionais no modulo `Banco de dados`:
    - tunnel SSH gerenciavel (start/stop/status);
    - execucao de comandos `psql` remotos;
    - sincronizacao via biblioteca Django (`dumpdata/loaddata`) para DEV.
  - limitar operacoes ao contexto `dev/hybrid` para reduzir risco operacional direto em modo estritamente produtivo.
- Consequencia:
  - operador admin consegue manter ciclo de backup/restore/sync sem acesso manual continuo ao terminal.
  - continuidade de evolucao do schema (novas migrations/tabelas/campos) fica coberta por dump logico + migrate pos-restore.

## 02/03/2026 - Instalacao hibrida com segredos locais e hardening de host
- Decisao:
  - executar instalacao no servidor por `installdev.sh` em modo sequencial (baixo consumo) com PostgreSQL local.
  - manter segregacao DEV/PROD com bancos distintos (`mrquentinha_dev` e `mrquentinha_prod`).
  - guardar segredo da maquina fora do repositorio em `/home/ubuntu/.mrquentinha-secure/host-secrets.env` e carregar no bootstrap.
  - limitar `*.trycloudflare.com` apenas ao ambiente DEV.
- Consequencia:
  - ambiente hibrido fica configurado para DNS/subdominios oficiais sem abrir `ALLOWED_HOSTS` de producao de forma excessiva.
  - continuidade de instalacao passa a ter checkpoint operacional em `.runtime/install/hybrid_install_state.json`.

## 26/02/2026 - Governanca de OAuth via Portal CMS (Google + Apple)
- Decisao:
  - centralizar parametros OAuth de client web e mobile em `PortalConfig.auth_providers`.
  - expor no payload publico somente campos seguros + flag `configured`, sem segredos.
  - manter configuracao sensivel editavel apenas no Admin Web (`/modulos/portal/autenticacao`).
- Consequencia:
  - habilitacao/desabilitacao de social login por ambiente sem rebuild do frontend.
  - reducao de risco de vazamento de credenciais no canal publico.
- Pendente tecnico:
  - implementar endpoint backend para troca de `code` Google/Apple por JWT local e validacao de `state`/nonce.

## 26/02/2026 - Template cliente `client-vitrine-fit` como opcao oficial do CMS
- Decisao:
  - adicionar template `client-vitrine-fit` na lista oficial do canal cliente com foco em merchandising visual (fotos grandes e grid densa).
  - manter convivencia com `client-classic` e `client-quentinhas` via seletor no Portal CMS.
- Consequencia:
  - operacao pode alternar layout do web client sem deploy e sem alterar o portal institucional em ownership Antigravity.

## 27/02/2026 - Cloudflare em DEV com dominios aleatorios
- Decisao:
  - adicionar `dev_mode` em `PortalConfig.cloudflare_settings` para permitir exposicao internet em desenvolvimento via URLs temporarias `trycloudflare`.
  - no `dev_mode`, nao exigir dominio real/subdominios/tunnel nomeado para publicar Portal/Client/Admin/API.
  - manter dominio real apenas para modo de operacao (`dev_mode=false`), preservando o fluxo de producao ja existente.
- Consequencia:
  - homologacao e testes externos podem ocorrer imediatamente sem bloqueio de DNS oficial.
  - configuracoes de conectividade (`api_base_url`, frontends e CORS) continuam sincronizadas automaticamente no backend quando `auto_apply_routes` estiver ativo.
  - o mesmo modulo de Cloudflare no Web Admin atende todos os templates do painel, sem necessidade de variacao por template.

## 27/02/2026 - Operacao Cloudflare por terminal com sync de frontends
- Decisao:
  - disponibilizar scripts oficiais para operar os mesmos fluxos do Web Admin via terminal (`status`, toggle DEV/PROD, runtime e preview).
  - padronizar sincronizacao de `.env.local` dos frontends (`admin/client/portal`) com a URL da API vigente, evitando apontamento stale apos rotacao de `trycloudflare`.
  - ajustar scripts de start do admin e client para priorizar `NEXT_PUBLIC_API_BASE_URL` vindo de `.env.local`.
- Consequencia:
  - a troca de endpoint da API em DEV/PROD passa a ser reprodutivel por CLI e sem edicao manual de arquivo.
  - o operador consegue alternar entre testes externos e configuracao de deploy tipico mantendo consistencia de enderecamento nos frontends.

## 27/02/2026 - Monitoramento de dominios DEV e refresh de URLs
- Decisao:
  - adicionar verificacao ativa de conectividade nos dominios aleatorios (`trycloudflare`) por servico (`portal/client/admin/api`) durante o status do runtime.
  - expor no Web Admin status, HTTP, latencia, URL checada e timestamp por servico.
  - incluir acao de runtime `refresh` para regenerar dominios aleatorios com um clique e reaplicar configuracao automaticamente.
- Consequencia:
  - operacao passa a validar se os dominios DEV estao realmente acessiveis sem sair do painel.
  - troca de URL temporaria fica controlada e repetivel, reduzindo risco de frontends apontarem para endpoint antigo.

## 27/02/2026 - Sincronizacao automatica na rotacao de trycloudflare
- Decisao:
  - sempre que o `status` do runtime detectar dominio DEV diferente do salvo, atualizar `cloudflare_settings.dev_urls` e reaplicar automaticamente `api_base_url` + URLs de frontends no `PortalConfig` (com `auto_apply_routes` ativo).
  - aceitar `*.trycloudflare.com` no `ALLOWED_HOSTS` do ambiente `dev` para garantir respostas da API via dominio aleatorio.
- Consequencia:
  - elimina drift entre dominio atual do tunnel e configuracao consumida pelos frontends.
  - evita erro `DisallowedHost` no backend durante homologacao online em modo DEV.

## 28/02/2026 - Workflow continuo de atualizacao do instalador
- Decisao:
  - instituir guard rail dedicado `scripts/check_installer_workflow.sh` para trilhas criticas de instalacao/deploy.
  - integrar o guard no fluxo de inicializacao e qualidade (`session.sh`, `sync_memory.sh`, `quality_gate_all.sh`).
  - exigir sincronizacao de memoria operacional junto com evolucao do instalador.
- Consequencia:
  - o instalador passa a evoluir de forma rastreavel quando mudam componentes criticos da aplicacao.
  - reduz risco de drift entre capacidades reais do ecossistema e fluxo guiado do Web Admin.

## 28/02/2026 - Assistente de instalacao no Web Admin (wizard guiado)
- Decisao:
  - criar o painel `Assistente de instalacao` no modulo `Administracao do servidor`.
  - adotar UX em passos curtos com validacao por etapa, autosave de draft e monitoramento de jobs.
  - manter reuso do script oficial `scripts/install_mrquentinha.sh` como engine principal da execucao local.
- Consequencia:
  - operadores nao tecnicos passam a configurar e iniciar o fluxo com menor friccao.
  - a automacao cloud/SSH pode evoluir por fases sem quebrar o contrato do wizard ja publicado.

## 28/02/2026 - Auditoria administrativa e URL mode do Cloudflare DEV
- Decisao:
  - criar app dedicado `admin_audit` no backend para trilha de uso do Web Admin com endpoint de consulta paginada.
  - registrar operacoes administrativas com sanitizacao de payload/query sensivel e sem auto-registro do endpoint da propria auditoria.
  - evoluir `cloudflare_settings` com `dev_url_mode` (`random`/`manual`) e `dev_manual_urls` editaveis no painel de conectividade.
- Consequencia:
  - operacao passa a ter historico rastreavel de quem fez o que e quando no Web Admin.
  - homologacoes longas (inclusive build mobile) podem usar enderecamento DEV fixo/manual sem perder opcao de dominios aleatorios.
  - sincronizacao de URLs de API/frontends no modo DEV permanece automatica e centralizada no backend.

## 01/03/2026 - Execucao remota do instalador (A5-A1)
- Decisao:
  - habilitar execucao remota real via SSH no `start_installer_job`, mantendo o mesmo script oficial `scripts/install_mrquentinha.sh`.
  - bloquear inicio de plano cloud (`aws`/`gcp`) sem validacao de conectividade/credencial de CLI no servidor backend.
  - sanitizar `ssh.password` em persistencia de `installer_settings` e payload de job.
- Consequencia:
  - fluxo remoto passa de "planejado" para "executavel" em SSH com monitoramento em background.
  - evita sinal verde falso em AWS/GCP quando o ambiente operador nao esta preparado.
  - reduz risco de vazamento de segredo em estado persistido do assistente.

## 01/03/2026 - Governanca completa de usuarios internos no Web Admin
- Decisao:
  - evoluir `Usuarios e RBAC` para administracao completa de contas (criacao/edicao), papeis e tarefas operacionais por categoria.
  - adicionar catalogo de tarefas no backend (`UserTaskCategory`, `UserTask`, `UserTaskAssignment`) e endpoints administrativos dedicados.
  - bloquear modulos tecnicos (`Portal CMS`, `Administracao do servidor`, `Instalacao / Deploy`, `Usuarios e RBAC`) para perfis sem `ADMIN`.
- Consequencia:
  - perfis operacionais ficam restritos ao escopo necessario da rotina diaria.
  - atribuicao de funcao administrativa continua centralizada em administradores.
  - base pronta para evoluir compliance operacional por tarefa e responsabilidade.

## 01/03/2026 - Priorizacao cloud AWS com paridade futura GCP
- Decisao:
  - iniciar trilha cloud automatica pelo AWS no assistente de instalacao/deploy.
  - manter paridade funcional planejada para Google Cloud na etapa seguinte.
  - explicitar custos por etapa no Web Admin (estimativa e consumo real quando disponivel).
- Consequencia:
  - fluxo cloud passa a ter caminho de implantacao incremental e auditavel.
  - backlog futuro ja orientado para replicacao em GCP e testes operacionais guiados fim a fim.

## 01/03/2026 - Auditoria administrativa como modulo proprio do Web Admin
- Decisao:
  - remover a secao de auditoria de `Administracao do servidor`.
  - criar modulo dedicado `Auditoria de atividade` com dashboard/KPIs, filtros, seguranca e tendencias.
  - evoluir API `admin_audit` com endpoint de overview para agregacoes de analise operacional.
- Consequencia:
  - governanca de auditoria passa a ter identidade funcional propria e UX mais objetiva.
  - administracao de servidor volta a foco exclusivo de infraestrutura (email, conectividade e release).
  - base pronta para evoluir alertas e compliance operacional.

## 01/03/2026 - Padrao global de formularios com CEP Correios e validacao forte
- Decisao:
  - evoluir o `FormFieldGuard` como camada global para `CEP`, `telefone`, `CPF/CNPJ`, `email` em tempo real.
  - criar endpoint backend `GET /api/v1/accounts/lookup-cep/` para lookup de CEP com fonte principal Correios e fallback opcional por configuracao.
  - reforcar validacao servidor-side de CPF/CNPJ por DV em `accounts` e `portal`.
  - persistir `phone_is_whatsapp` em `UserProfile` para uso operacional no Admin.
- Consequencia:
  - menos erro de digitacao em formularios e padrao consistente entre templates/canais.
  - seguranca de dados elevada por validacao no cliente e no servidor.
  - novos formularios devem seguir o mesmo contrato sem implementar validacao local ad-hoc.

## 01/03/2026 - Criptografia de dados sensiveis em `UserProfile`
- Decisao:
  - adotar `EncryptedTextField` para dados sensiveis com hashes de busca.
  - controlar chaves por ambiente (`FIELD_ENCRYPTION_KEY`, `FIELD_HASH_SALT`) e strict mode opcional.
  - registrar decisão formal no ADR `0018-criptografia-dados-sensiveis-userprofile.md`.
- Consequencia:
  - dados sensiveis ficam protegidos em repouso, mantendo buscas administrativas por hash.
  - ambiente precisa gerenciar chaves e rotacao com cuidado.

## 02/03/2026 - Bancos separados DEV/PROD com seed controlado
- Decisao:
  - manter bancos fisicamente separados para DEV e PROD (`mrquentinha_dev` e `mrquentinha_prod`).
  - DEV pode receber dump do ambiente local para testes; PROD inicia zerado com defaults minimos (`seed_portal_default`).
  - padronizar setup via script `installdev.sh` e guia AWS preconfig.
- Consequencia:
  - evita vazamento de dados de teste para producao.
  - exige disciplina operacional para alternar `.env` e executar migrations corretas.

## 27/02/2026 - Confirmacao de e-mail com URL dinamica por ambiente
- Decisao:
  - tornar e-mail obrigatorio no cadastro do cliente (`/api/v1/accounts/register/`) e disparar confirmacao por token.
  - gerar link de confirmacao sempre para o frontend web cliente (`/conta/confirmar-email`), priorizando origem atual da requisicao em DEV (IP/local ou `trycloudflare`) e fallback para `PortalConfig.client_base_url`.
  - persistir rastreabilidade em `UserProfile` (token hash, timestamps e ultima base URL usada no envio).
  - expor no Admin Web indicadores de conformidade por usuario (`email_verified` + pendencias de dados essenciais para autenticacao/pagamento).
- Consequencia:
  - rotacao de dominios dinamicos no DEV nao quebra o fluxo de confirmacao, desde que seja reenviado e-mail.
  - modo producao permanece aderente ao DNS oficial configurado no CMS.
  - operacao passa a identificar no painel de usuarios quem ainda nao concluiu validacao e quais campos faltam para jornada de pagamento autenticado.

## 27/02/2026 - Bloqueio de login cliente sem e-mail validado + token de 3h
- Decisao:
  - bloquear emissao de JWT em `/api/v1/accounts/token/` para contas com role `CLIENTE` sem `email_verified_at`.
  - tornar reenvio de token acessivel no fluxo de login sem sessao (`identifier` por usuario/e-mail).
  - reduzir TTL do token de confirmacao para 3 horas.
  - manter somente o ultimo token valido (rotacao por sobrescrita do hash no perfil).
- Consequencia:
  - conta recem-cadastrada nao acessa checkout/login pleno sem validacao de e-mail.
  - UX de recuperacao fica autoatendida direto na tela de login.
  - reduz risco de uso de links antigos apos reenvios sucessivos.

## 26/02/2026 - Configuracao multigateway de pagamentos via Portal CMS
- Decisao:
  - centralizar no `PortalConfig.payment_providers` as credenciais e roteamento de Mercado Pago, Efi e Asaas.
  - permitir no Admin Web selecao de um ou varios providers ativos, ordem por metodo (`PIX`, `CARD`, `VR`) e dados do recebedor (`CPF/CNPJ`).
  - manter segredos apenas no canal admin; payload publico entrega somente campos seguros + `configured`.
  - padronizar callbacks com endpoints dedicados por provider (`/webhook/mercadopago`, `/webhook/asaas`, `/webhook/efi`) reaproveitando reconciliacao idempotente existente.
- Consequencia:
  - operacao consegue trocar gateway sem rebuild do client/mobile.
  - checkout no web client passa a habilitar metodos dinamicamente por configuracao publicada.
- Pendente tecnico:
  - homologacao externa com credenciais reais dos tres providers.
  - endurecimento de assinatura/validacao de webhook especifica por provider.

## 26/02/2026 - Roteamento de gateway por canal e monitoramento realtime
- Decisao:
  - restringir selecao de gateway para **um provider por frontend** (`web` e `mobile`) em `payment_providers.frontend_provider`.
  - propagar canal de origem via header (`X-Client-Channel`) para resolver provider em runtime no backend.
  - publicar endpoint operacional unico `GET /api/v1/orders/ops/realtime/` para monitorar saude de servicos, comunicacao com gateways e lifecycle de pedidos.
- Consequencia:
  - roteamento previsivel por canal sem depender apenas de ordem por metodo.
  - dashboard e modulo de monitoramento no Admin com visao central de operacao/pagamentos em tempo real.
  - base pronta para homologacao externa (`A4`) com observabilidade minima ja ativa.

## 26/02/2026 - T8.2.2 implementado (financas pessoais evolucao MVP)
- Recorrencia:
  - adotado modelo `PersonalRecurringRule` com `frequency` (`WEEKLY`/`MONTHLY`) e `next_run_date`.
  - idempotencia garantida por `PersonalEntry.recurring_event_key` + unique (`owner`, `recurring_event_key`).
  - materializacao publicada em `POST /api/v1/personal-finance/recurring-rules/materialize/`.
- Resumo mensal:
  - consolidacao por competencia (`month=YYYY-MM`) com totais `IN/OUT`, saldo, top categorias e status de budget.
  - endpoint publicado em `GET /api/v1/personal-finance/summary/monthly/`.
- Importacao CSV:
  - fluxo em duas etapas (`preview` -> `confirm`) com `PersonalImportJob`.
  - deduplicacao por hash canonico (`PersonalEntry.import_hash`) com unique (`owner`, `import_hash`).
  - endpoints publicados em `POST /api/v1/personal-finance/imports/preview/` e `POST /api/v1/personal-finance/imports/<id>/confirm/`.

## Etapa 3.1 - Geracao de requisicao por cardapio
- Multiplicador de consumo no MVP:
  - se `MenuItem.available_qty` estiver preenchido, usar esse valor para multiplicar os ingredientes da receita.
  - se `available_qty` estiver vazio, considerar `1` lote por prato.
- Conversao de unidade:
  - nao implementar nesta etapa.
  - service valida compatibilidade entre `DishIngredient.unit` e unidade base do ingrediente/estoque.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) em etapa futura.

## Decisoes abertas para Etapas 6-8
- Stack do portal institucional (Etapa 6):
  - decidir entre Next.js (SSR/SSG) ou estrutura estatica mais simples.
  - definir nivel de integracao com autenticacao e acesso ao admin.
- Estrategia de web clientes/PWA (Etapa 7):
  - definir escopo minimo do PWA (instalacao, cache, offline parcial, push).
  - definir paridade funcional entre mobile nativo e canal web.
- Segregacao de dados pessoais (Etapa 8):
  - definir separacao logica/fisica entre dados operacionais da empresa e dados pessoais sensiveis.
  - definir politicas de retencao, mascaramento e trilha de auditoria aderentes a LGPD.

## Decisoes abertas para Finance (Etapa 5)
- Padrao de integracao AP/AR/Caixa por referencia:
  - adotar `reference_type` + `reference_id` como contrato unico entre dominios operacionais e financeiro.
  - mapear origens minimas: `PURCHASE` -> AP, `ORDER` -> AR, liquidacao -> Caixa.
- Idempotencia por referencia:
  - definir unique composta por tipo e id de referencia no financeiro para evitar duplicidade de lancamentos.
  - decidir comportamento em reprocessamento (ignorar duplicado vs atualizar registro existente).
- Producao na subfase 5.4:
  - criar app dedicado `production` para consolidar rotina operacional e fechamento diario.
  - decidir fronteira entre `orders`, `inventory` e `production` para evitar sobreposicao de responsabilidades.

## TODO Etapa 5 - AR a partir de Order
- Gerar `finance_ar_receivable` automaticamente a partir de `Order` confirmado.
- Usar referencia padrao:
  - `reference_type = ORDER`
  - `reference_id = <order.id>`
- Definir gatilho exato de criacao no fluxo (ex.: `CONFIRMED` ou `DELIVERED`).

## Etapa 5.0 - padrao financeiro implementado
- Contrato de integracao entre dominios:
  - `reference_type` + `reference_id` como referencia cruzada entre operacional e financeiro.
- Idempotencia em AP/AR:
  - `APBill` e `ARReceivable` com unique por referencia quando preenchida.
  - services retornam registro existente ao receber a mesma referencia.
- Caixa na fundacao:
  - `CashMovement` mantem referencia opcional da origem.
  - services de caixa aplicam idempotencia por referencia (`AR` e `AP`) para evitar duplicidade em reprocessamento.
- Integracoes planejadas para proximas subfases:
  - 5.1: consolidar geracao de AP a partir de `Purchase`.
  - 5.2: consolidar geracao de AR a partir de `Order`/`Payment`.

## Etapa 5.1 - Regra idempotente de AP por compra
- Gatilho de integracao:
  - o service `create_purchase_and_apply_stock` passa a chamar `finance.services.create_ap_from_purchase` ao final da criacao da compra.
- Contrato de referencia para AP de compras:
  - `reference_type = "PURCHASE"`
  - `reference_id = <purchase.id>`
- Idempotencia aplicada em camada de service (antes de depender apenas da constraint):
  - se ja existir `APBill` com a referencia da compra, o service retorna o registro existente.
  - comportamento definido para reprocessamento: nao duplica titulo financeiro.
- Regra de valor do AP (MVP):
  - usar `Purchase.total_amount` quando maior que zero.
  - fallback para soma de itens (`qty * unit_price + tax_amount`) quando total vier zerado.

## Etapa 5.2 - Idempotencia de cash-in por AR
- Integracao `Order -> AR`:
  - todo pedido criado deve gerar (ou reaproveitar) um `ARReceivable` por referencia `ORDER` + `order.id`.
  - conta padrao do AR no MVP: `Vendas` (REVENUE).
- Integracao `Payment PAID -> AR -> Caixa`:
  - ao marcar pagamento como `PAID`, localizar AR pela referencia do pedido.
  - AR deve ser marcado como `RECEIVED`.
  - registrar `CashMovement` de entrada com referencia `AR` + `ar.id`.
  - conta padrao de caixa para entrada: `Caixa/Banco` (ASSET).
- Regra idempotente obrigatoria:
  - se o AR ja estiver recebido e/ou ja existir movimento `IN` referenciado ao AR, nao gerar novo movimento.
  - reprocessamento de pagamento `PAID` deve ser seguro e sem duplicidade financeira.

## Etapa 5.3 - Cashflow (MVP)
- Relatorio de caixa por periodo usa agregacao diaria de `CashMovement`.
- Decisao MVP sobre dias sem movimento:
  - dias sem movimentacao nao sao retornados no endpoint de cashflow.
  - motivo: resposta mais enxuta no MVP, mantendo foco nos dias com evento financeiro.
  - TODO futuro: opcao para preencher dias vazios com zero quando necessario para dashboards.

## Etapa 5.4 - Producao e consumo de estoque
- Integracao de referencia em estoque para producao:
  - `StockMovement.reference_type = "PRODUCTION"`
  - `StockMovement.reference_id = <production_batch.id>`
- Idempotencia no fechamento do lote:
  - `complete_batch` nao deve gerar novos movimentos se o lote ja estiver `DONE`.
  - se ja houver movimentos `OUT` de referencia `PRODUCTION` para o lote, apenas conclui status e retorna.
- Unidade sem conversao (MVP):
  - consumo de ingrediente em producao exige unidade compativel entre receita (`DishIngredient.unit`) e estoque/ingrediente.
  - ao detectar unidade incompativel, o service retorna `ValidationError` explicita.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) em subfase futura.

## Etapa 5.5 - Custos, margem e DRE simplificada
- Base de receita no MVP:
  - a receita dos relatorios (`DRE` e `KPIs`) considera pedidos com status `DELIVERED` no periodo.
- CMV do MVP:
  - calculado como custo estimado dos itens vendidos (`OrderItem.qty * custo_menu_item`).
  - nao usa consumo real de estoque nesta fase.
  - TODO futuro: comparar custo estimado vs custo real (com base em movimentos de producao/estoque).
- Custo de ingrediente:
  - media ponderada por compras (`PurchaseItem`): `sum(qty * unit_price + tax) / sum(qty)`.
- Sem conversao de unidades no MVP:
  - divergencia entre unidade de compra/receita e unidade base do ingrediente gera `ValidationError` explicita.
  - TODO: implementar conversao de unidades (g<->kg, ml<->l, etc.) para custos reais e comparaveis.

## Etapa 5.6.1 - Ledger de auditoria financeira
- Escopo do ledger no MVP:
  - registrar trilha de auditoria financeira orientada a eventos do AP/AR/Caixa.
  - nao substitui contabilidade completa (livro diario/razao) nesta fase.
- Decisao de lancamento por evento:
  - para recebimento de AR, registrar duas entradas: `AR_RECEIVED` e `CASH_IN`.
  - para pagamento de AP, registrar duas entradas: `AP_PAID` e `CASH_OUT`.
  - motivo: manter visao de evento de negocio e evento de caixa separadas para auditoria operacional.
- Idempotencia do ledger:
  - chave unica em (`reference_type`, `reference_id`, `entry_type`).
  - services usam `get_or_create` para reprocessamento seguro sem duplicidade.
- TODO futuro:
  - evoluir para modelo contabil completo com partidas dobradas obrigatorias e fechamento por periodo.

## Etapa 5.6.2 - Conciliacao de caixa (extrato)
- Modelo de conciliacao MVP:
  - conciliacao manual via vinculo `CashMovement.statement_line`.
  - flag `CashMovement.is_reconciled` indica pendencia/conciliado para filtros operacionais.
- Regra de idempotencia:
  - reconciliar o mesmo movimento com a mesma `StatementLine` e operacao idempotente.
  - se o movimento ja estiver conciliado com outra linha, o service retorna erro claro (nao sobrescreve).
- Reconciliacao inversa:
  - `unreconcile_cash_movement` remove vinculo e volta `is_reconciled=false`.
- Relatorio de pendencias:
  - endpoint `reports/unreconciled` retorna apenas movimentos nao conciliados por periodo (`from`/`to`).

## Etapa 5.6.3 - Fechamento por periodo (MVP)
- Escopo de bloqueio no MVP:
  - bloqueio aplicado no service layer (sem trigger no banco nesta etapa).
  - alteracoes em `CashMovement`, `APBill`, `ARReceivable` e `LedgerEntry` sao barradas quando a data relevante estiver em periodo fechado.
- Snapshot no fechamento:
  - `FinancialClose.totals_json` registra totais congelados do periodo no momento do fechamento.
  - totais incluem DRE (`receita_total`, `despesas_total`, `cmv_estimado`, `lucro_bruto`, `resultado`) e caixa (`saldo_caixa_periodo`, `saldo_caixa_final`).
- Regra de duplicidade:
  - nao permitir fechar o mesmo intervalo (`period_start`, `period_end`) duas vezes.
  - comportamento definido: retornar erro de validacao claro no service `close_period`.

## 24/02/2026 - Midia, OCR e dados DEMO ponta a ponta
- Midia (MVP dev):
  - imagens armazenadas em `MEDIA_ROOT` local com `MEDIA_URL=/media/`.
  - uploads expostos por endpoints dedicados (ingrediente, prato, comprovante de compra e OCR job).
  - decisao de nao usar S3/CDN nesta fase; migracao para storage externo fica para fase de deploy/producao.

- OCR (MVP funcional):
  - pipeline com fallback:
    - prioridade para `pytesseract` quando disponivel;
    - fallback para modo simulado com `raw_text` enviado na requisicao.
  - parser MVP extrai campos principais de rotulo e comprovante para `parsed_json`.
  - aplicacao de OCR (`/ocr/jobs/<id>/apply/`) suporta `merge` e `overwrite`.

- Nutricao (MVP):
  - dados em `NutritionFact` por 100g/ml e por porcao opcional.
  - sem conversao de unidades nesta fase; divergencia gera erro claro + TODO.
  - referencia normativa documentada: RDC 429/2020 e IN 75/2020.
  - escopo restrito a dados capturados/estimados + fonte, sem alegacoes nutricionais de marketing.

- Seed DEMO:
  - comando `seed_demo` cobre cadeia completa: catalogo, compras, estoque, producao, pedidos, financeiro e OCR simulado.
  - comportamento idempotente para repeticao em ambiente de desenvolvimento.

- UI compartilhada (portal/client):
  - pacote comum em `workspaces/web/ui` com componentes base e `TemplateProvider`.
  - frontends configurados para usar visual "clean" com tokens da marca.
  - build dos apps web padronizado com `next build --webpack` para compatibilidade com pacote compartilhado local.

## 24/02/2026 - Catalogo publico read-only para smoke/frontends
- Contexto:
  - apos hardening de Auth/RBAC, o smoke do stack e os frontends passaram a receber `401` em `GET /api/v1/catalog/menus/`.
- Decisao MVP:
  - manter RBAC/`IsAuthenticated` como padrao em catalogo.
  - liberar apenas leitura publica minima de cardapio:
    - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
    - `GET /api/v1/catalog/menus/today/`
- Justificativa:
  - portal/client precisam de consulta publica de cardapio no MVP.
  - nao ha liberacao de CRUD (`ingredients`, `dishes`, `menus` list/create/update/delete) para anonimos.
- Risco controlado:
  - superficie publica limitada somente a leitura de cardapio.
- Opcao futura (nao implementada nesta etapa):
  - smoke autenticado via JWT para cobrir fluxos privados com perfil de teste.

## 24/02/2026 - Politica de branches Codex x Antigravity x Join
- `BRANCH_CODEX_PRIMARY=feature/etapa-4-orders`.
- Codex opera somente em `BRANCH_CODEX_PRIMARY`.
- Antigravity opera somente em `ag/<tipo>/<slug>`.
- Integracao entre agentes ocorre em `join/codex-ag`.
- Guard rail operacional:
  - `scripts/branch_guard.sh` em modo `--strict` antes de checkpoint/sync/merge.

## 24/02/2026 - Harmonizacao de workflows Codex <-> Antigravity
- Arquitetura de workflows:
  - `W10..W21` = fonte de verdade (rotinas completas).
  - `00..06` = wrappers de entrada, sem duplicar instrucoes longas.
- Politica de branch em workflow com escrita:
  - qualquer fluxo com `commit/push/merge` deve validar branch com `scripts/branch_guard.sh` antes de prosseguir.
- Modo paralelo:
  - lock humano obrigatorio por contexto em `.agent/memory/IN_PROGRESS.md` para evitar edicao concorrente dos mesmos arquivos.
  - sincronizacao obrigatoria pre-checkpoint via `W21_sync_codex_antigravity`.
- Confiabilidade de comandos:
  - testes no root exigem venv backend ativa.
  - comandos npm exigem `source ~/.nvm/nvm.sh && nvm use --lts`.

## 24/02/2026 - Sincronismo GEMINI (repo -> global)
- Fonte oficial versionada:
  - `~/mrquentinha/GEMINI.md`
- Fonte runtime para Antigravity UI:
  - `~/.gemini/GEMINI.md`
- Regra:
  - o arquivo do repo e a fonte de verdade.
  - o arquivo global deve ser sincronizado automaticamente via `scripts/sync_gemini_global.sh`.
- Excecao permitida:
  - `GEMINI.md` do repo pode conter cabecalho de espelho; o conteudo canonico (pos-cabecalho) deve ser identico ao global.
- Validacao obrigatoria em sync:
  - checar chaves `BRANCH_CODEX_PRIMARY`, `BRANCH_ANTIGRAVITY` e `BRANCH_UNION`.

## 24/02/2026 - GEMINI global-only (fonte unica)
- Decisao:
  - a unica fonte de regra global e branch policy passa a ser `/home/roberto/.gemini/GEMINI.md`.
  - workflows e scripts nao dependem mais de `GEMINI.md` do repositorio.
- Implicacoes:
  - validacao obrigatoria via `bash scripts/gemini_check.sh` antes de fluxos com escrita.
  - `scripts/sync_gemini_global.sh` permanece apenas como stub deprecado.
  - snapshot em `docs/memory/GEMINI_SNAPSHOT.md` e opcional, somente para documentacao.

## 25/02/2026 - Planejamento mestre (docs-first)

### Decisao: Postgres + JSONField para CMS e nutricao variavel
- Status: aceito.
- Contexto: Portal CMS e campos de nutricao/OCR possuem estrutura parcialmente variavel por template/fonte.
- Decisao:
  - manter Postgres como banco unico.
  - usar `JSONField` para blocos dinamicos de CMS (config/sections por template/pagina) e payloads variaveis de OCR/nutricao.
- Consequencia:
  - maior flexibilidade no MVP sem proliferar migracoes para cada variacao de bloco.
  - exigir validacao em service/serializer para garantir contrato de leitura no frontend.

### Decisao: Politica de endpoints publicos x privados
- Status: aceito.
- Decisao:
  - publico read-only: `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`, `GET /api/v1/catalog/menus/today/`, health/index.
  - privado autenticado (RBAC): operacoes de escrita e dados operacionais internos.
  - CMS publico (planejado 6.3): somente leitura de secoes aprovadas/publicadas.
- Consequencia:
  - reduz superficie anonima e preserva distribuicao publica do cardapio/portal.

### Decisao: Estrategia de templates e ownership entre agentes
- Status: aceito.
- Decisao:
  - template visual do portal (6.2) segue ownership primario do Antigravity enquanto houver lock ativo.
  - Codex prioriza backend, client, pagamentos, CMS backend-only e Admin Web para evitar conflito de layout.
  - integracao entre trilhas via `Antigravity_Codex` + testes completos.
- Consequencia:
  - menor risco de retrabalho em UI e merges mais previsiveis.

### Decisao: Estrategia do Admin Web (epico obrigatorio)
- Status: aceito.
- Decisao:
  - criar trilha dedicada de Admin Web (`9.0` MVP e `9.1` completo), desacoplada do portal institucional.
  - Admin Web cobre modulos operacionais internos (Dashboard, Cardapio, Compras, Estoque, Producao, Pedidos, Financeiro, Portal CMS, Usuarios/RBAC, Relatorios).
  - compartilhar componentes/tokens via `workspaces/web/ui` quando aplicavel.
- Consequencia:
  - clareza de fronteira entre canal institucional (portal), canal cliente (client) e canal interno (admin).

## 25/02/2026 - Contrato do Portal CMS backend-only (T6.3.1)
- Status: aceito.
- Decisao:
  - app dedicado `portal` no backend para concentrar configuracao e secoes do portal institucional.
  - configuracao global em `PortalConfig` (singleton) e conteudo por template/pagina em `PortalSection` com `JSONField`.
  - API publica read-only para render do portal:
    - `GET /api/v1/portal/config/`
    - `GET /api/v1/portal/config/version`
  - API de administracao mantida autenticada (MVP) via endpoints `admin/config` e `admin/sections`.
- Consequencia:
  - desacopla conteudo do portal institucional do frontend.
  - prepara terreno para a etapa `T6.3.2` (portal consumindo CMS) sem bloquear trilha visual do Antigravity.

## 26/02/2026 - Evolucao faseada de Financas Pessoais (T8.2.1)
- Status: aceito.
- Decisao:
  - manter evolucao da trilha `personal_finance` por fases incrementais, sem acoplar ao modulo `finance`.
  - priorizar na proxima fase tecnica (`T8.2.2`):
    - recorrencia de lancamentos;
    - resumo mensal por categoria/totais;
    - importacao CSV com preview e confirmacao.
  - manter contratos da API no namespace `/api/v1/personal-finance/...`.
- Consequencia:
  - ganho funcional orientado ao usuario final com risco tecnico controlado.
  - preserva segregacao de dados e fronteira arquitetural definida nos ADRs `0003` e `0005`.

## 27/02/2026 - Escopo de validacao de e-mail e gestao SMTP no Admin (T9.2.1-A2-HF6)
- Status: aceito.
- Decisao:
  - validacao obrigatoria de e-mail passa a ser regra exclusiva do canal cliente.
  - usuarios administrativos/gestao nao devem ser bloqueados no login por falta de `email_verified_at`.
  - configuracao de e-mail operacional/smtp passa a ser centralizada no `PortalConfig.email_settings`, gerenciavel no Web Admin com endpoint de teste dedicado.
- Consequencia:
  - evita regressao de acesso no Web Admin.
  - reduz dependencia de ajuste manual de `.env` para operacao de e-mail.
  - mantem compliance no canal cliente sem impactar operacao interna.

## 01/03/2026 - Validacao AWS segura no assistente de instalacao (T9.2.7-A5-A2)
- Status: aceito.
- Decisao:
  - adicionar endpoint dedicado de validacao AWS no modulo `Instalacao / Deploy`:
    - `POST /api/v1/portal/admin/config/installer-cloud/aws/validate/`;
  - validar credenciais AWS por dois modos:
    - `profile` (role/perfil local),
    - `access_key` (chaves temporarias/em runtime);
  - nunca persistir `secret_access_key` e `session_token` no `PortalConfig`/jobs.
  - incluir no retorno da validacao:
    - conectividade (`STS`/`IAM`),
    - checks de infraestrutura (`Route53`, `EC2`, `Elastic IP`, `CodeDeploy`),
    - custos estimados e snapshot MTD via Cost Explorer (quando habilitado).
- Consequencia:
  - operador ganha visibilidade tecnica e financeira antes do provisionamento cloud.
  - fluxo AWS fica mais seguro por reduzir persistencia de segredos.
  - automacao completa de provisionamento/deploy permanece na proxima iteracao.
- Referencia:
  - ADR `docs/adr/0016-installer-aws-validacao-segura-e-custos.md`.

## 01/03/2026 - Links operacionais no Portal CMS para onboarding de providers (T9.2.7-A5-A2-HF1)
- Status: aceito.
- Decisao:
  - incluir, no `Portal CMS`, blocos de links externos para orientar operadores sobre:
    - cadastro/configuracao de Google e Apple (OAuth social);
    - cadastro/configuracao de Mercado Pago, Efi e Asaas (pagamentos).
  - manter os links dentro do proprio contexto de configuracao, reduzindo troca de tela e erro de preenchimento.
- Consequencia:
  - operadores conseguem levantar credenciais e referencias oficiais sem sair do fluxo do Web Admin.
  - menor tempo de setup para primeira configuracao de autenticacao e gateways.

## 04/03/2026 - Protocolo operacional triagente Mac->VM->EC2
- Status: aceito.
- Decisao:
  - formalizar workflow dedicado `W27_sync_mac_vm_ec2` para coordenacao continua entre agentes.
  - toda demanda iniciada pelo Agente Mac deve ser implementada e testada primeiro na VM (`vm-atualizacoes`), com aplicacao em EC2 somente apos aprovacao.
  - quando operador atuar diretamente na VM ou EC2, o Mac deve sincronizar no primeiro contato seguinte e registrar no `AGENT_SYNC_BOARD`.
  - preservar publicacao por branch fixa:
    - Mac -> `codex/AgenteMac`
    - VM -> `vm-atualizacoes`
    - EC2 -> `main`
- Consequencia:
  - reduz conflito entre trabalhos individuais e evita promocao de mudanca sem validacao previa no ambiente dev.
  - melhora rastreabilidade entre pedido, validacao, aprovacao e publicacao final.

## 04/03/2026 - Autenticacao operacional dos agentes e promocao controlada do hotfix de sessao no Admin
- Status: aceito.
- Decisao:
  - padronizar acesso operacional dos agentes por chave SSH (sem dependencia de senha interativa):
    - `github.com` com chaves locais do operador;
    - `mrquentinha` e `mrquentinha_web` com `IdentityFile` explicito e `ForwardAgent` habilitado no Mac;
    - chave publica do Mac registrada no `authorized_keys` da VM para eliminar prompt de senha.
  - promover o hotfix de menu/sessao do Admin em ordem obrigatoria:
    - VM (`vm-atualizacoes`) validada primeiro;
    - EC2 (`main`) somente apos build e smoke checks de producao.
- Consequencia:
  - fluxo de coordenacao entre agentes fica mais rapido e previsivel, com menos risco de bloqueio por autenticacao.
  - publicacao em producao preserva o principio de aprovacao previa na VM e impacto minimo de disponibilidade.


## 05/03/2026 - Alinhamento de governanca triagente com baseline de commits do hotfix admin
- Status: aceito.
- Decisao:
  - adotar como baseline oficial do ciclo de sincronizacao os commits informados pelo Agente Mac:
    - Mac (`codex/AgenteMac`): `b8acf4b`;
    - VM (`vm-atualizacoes`): `8a4e81b`;
    - EC2 (`main`): `abda7d1`.
  - manter regra obrigatoria de promocao `Mac -> VM (execucao/teste) -> EC2 (promocao)`.
  - tratar indisponibilidade de SSH/DNS no ambiente de coordenacao como risco operacional temporario, sem promover nova mudanca ate evidencia remota da VM.
- Consequencia:
  - memoria viva fica alinhada ao estado mais recente esperado para os tres agentes.
  - proxima acao unica passa a ser a validacao remota da VM com smoke antes de qualquer nova promocao em EC2.


## 06/03/2026 - Modo operacional do WebAdmin e diagnostico Cloudflare API no Admin do servidor
- Status: aceito.
- Decisao:
  - padronizar no modulo `Administracao do servidor` um seletor de modo operacional com tres estados:
    - `dev`: foco em rede local e testes controlados;
    - `producao`: desativa fluxo DEV random para reduzir risco em maquina publicada;
    - `hibrido`: permite coexistencia local + Cloudflare.
  - restringir dominios DEV random (`trycloudflare`) e refresh automatico desse fluxo ao modo `hibrido`.
  - incluir endpoint dedicado de diagnostico Cloudflare API para validacao operacional de token/zona/DNS com guia de ativacao e permissoes minimas.
- Consequencia:
  - operador passa a ter clareza de impacto por modo antes de salvar configuracoes no WebAdmin.
  - risco de alteracao acidental em producao e reduzido por bloqueio de fluxo random fora do modo hibrido.
  - onboarding Cloudflare fica opcional, guiado e auditavel diretamente no painel.
