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
