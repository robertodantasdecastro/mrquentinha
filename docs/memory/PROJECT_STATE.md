# Project State (dev)

Referencia de atualizacao: 27/02/2026.

## Etapas
- Concluidas: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`, `7.2.1`, `7.2.2`, `7.2.3`, `6.3.1`, `6.1.1`, `9.0.1`, `9.0.2`, `9.0.3`, `9.1.1`, `9.1.2`, `9.1.3-A7`, `9.2.6-A1`, `6.3.2-A3`, `6.3.2-A4`, `6.3.2-A5`, `6.3.2-A6`, `6.3.2-A7`, `6.3.2-A9`, `6.3.2-A10`, `6.3.2-A11`, `6.3.2-A12`, `6.3.2-A13`, `6.3.2-A14`, `8.0.1`, `8.1.1`, `8.1.2`, `8.2.1`, `8.2.2`.
- Em progresso: `6.2` (Portal template no fluxo Antigravity).
- Proxima execucao recomendada (unica): `T9.2.1-A2` (primeira rodada de testes manuais E2E).
- Status atual de execucao manual: `T9.2.1-A2` iniciado em 27/02/2026, com relatorio operacional aberto em `docs/memory/T9_2_1_A2_RELATORIO_EXECUCAO_2026-02-27.md`.

## Planejamento oficial (docs-first)
- Requisitos consolidados: `docs/memory/REQUIREMENTS_BACKLOG.md`
- Roadmap mestre: `docs/memory/ROADMAP_MASTER.md`
- Backlog priorizado: `docs/memory/BACKLOG.md`
- Fila operacional curta: `.agent/memory/TODO_NEXT.md`

## Politica de branches (anti-conflito)
- `BRANCH_CODEX_PRIMARY=main`
- `BRANCH_ANTIGRAVITY=AntigravityIDE`
- `BRANCH_UNION=Antigravity_Codex`
- Codex: `main` e `main-etapa-*`.
- Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`.
- Uniao: `Antigravity_Codex` (somente merge/cherry-pick/PR).
- Guard rail: `scripts/branch_guard.sh`.

## Antigravity / GEMINI
- Fonte unica GEMINI (runtime + policy): `/home/roberto/.gemini/GEMINI.md`
- Validacao obrigatoria: `bash scripts/gemini_check.sh`
- Rules path: `.agent/rules/global.md`
- Espelho topo: `.agent/rules/00_GLOBAL_RULE.md`
- Guia de uso: `.agent/workflows/USAGE_GUIDE.md`
- Mapa oficial: `.agent/workflows/WORKFLOW_MAP.md`

## Modo paralelo
- Regras: `docs/memory/PARALLEL_DEV_RULES.md`
- Lock humano: `.agent/memory/IN_PROGRESS.md`
- Sync obrigatorio: `W21_sync_codex_antigravity`
- Observacao: se `6.2 portal template` estiver ativo no Antigravity, Codex evita alteracao concorrente de layout no portal.

## Estado por componente

### Backend (Django)
- Status: operacional (Auth JWT, Finance MVP completo, OCR mock, nutricao, producao, relatorios).
- Banco: PostgreSQL (`mrquentinhabd`).
- Modulos ativos: `core`, `accounts`, `catalog`, `inventory`, `procurement`, `orders`, `finance`, `personal_finance`, `production`, `ocr_ai`, `portal`.
- Atualizacao concluida em 27/02/2026 (`T9.2.1-A2-HF4`): cadastro do cliente exige e-mail e envia confirmacao com link dinamico por ambiente; novos endpoints de confirmacao/reenvio e novos campos de compliance de usuario no payload admin.
- Atualizacao concluida em 27/02/2026 (`T9.2.1-A2-HF5`): login JWT de contas `CLIENTE` sem e-mail validado passou a ser bloqueado; reenvio de token disponivel por `identifier` no fluxo publico; token de confirmacao com TTL padrao de 3 horas.
- Pagamentos online (`7.2.1` + `7.2.2` + `7.2.3`):
  - `PaymentIntent` persistido com idempotencia por pagamento/chave.
  - provider abstraction inicial (`mock`) com payload de intent para PIX/CARD/VR.
  - webhook idempotente com reconciliacao para `AR/Cash/Ledger`.
  - criacao de pedido com `payment_method` (PIX/CARD/VR) para acionar checkout online por intent.
  - eventos de webhook persistidos em `PaymentWebhookEvent` para replay seguro por `provider + event_id`.
- Pagamentos multigateway (`T7.2.4-A1`):
  - `PortalConfig.payment_providers` passou a centralizar configuracao de Mercado Pago, Efi e Asaas (roteamento por metodo, providers habilitados e recebedor CPF/CNPJ).
  - selecao de provider por metodo (`PIX/CARD/VR`) em runtime via `apps/orders/provider_config.py`.
  - webhooks dedicados adicionados:
    - `POST /api/v1/orders/payments/webhook/mercadopago/`
    - `POST /api/v1/orders/payments/webhook/asaas/`
    - `POST /api/v1/orders/payments/webhook/efi/`
  - endpoint admin de teste de conectividade por provider:
    - `POST /api/v1/portal/admin/config/test-payment-provider/`
- Pagamentos multigateway (`T7.2.4-A2`):
  - configuracao `payment_providers.frontend_provider` aplicada por canal (`web`/`mobile`) com provider unico por frontend.
  - criacao de intent passou a receber `source_channel` (header `X-Client-Channel`) e resolver provider por canal antes da ordem por metodo.
- Observabilidade operacional (`T7.2.4-A3`):
  - endpoint `GET /api/v1/orders/ops/realtime/` publicado com saude de servidor, status dos servicos (`backend/admin/portal/client`), comunicacao com gateways e lifecycle de pedidos.
  - payload realtime inclui `frontend_provider` ativo por canal, metricas de webhooks/intents por provider e serie de 15 minutos para dashboard.
- Portal CMS mobile release (`T6.3.2-A6`):
  - `MobileRelease` persistido com status de pipeline, snapshot de `api_base_url` e host publico.
  - endpoint publico `GET /api/v1/portal/mobile/releases/latest/` para distribuir links de download.
  - endpoints admin para criar/compilar/publicar release em `/api/v1/portal/admin/mobile/releases/`.
- Portal CMS autenticacao social (`T6.3.2-A7`):
  - `PortalConfig` passou a expor `auth_providers` (Google/Apple) com parametros web/mobile gerenciados no Admin Web.
  - payload publico do CMS expoe apenas dados seguros e `configured`, sem `client_secret`/`private_key`.
  - template adicional `client-vitrine-fit` incluido no cadastro oficial de templates do canal cliente.
- Portal CMS conectividade cloud (`T6.3.2-A9`):
  - `PortalConfig` ganhou `cloudflare_settings` para governanca de dominio/tunnel/modo de exposicao.
  - novos endpoints admin para preview e toggle:
    - `POST /api/v1/portal/admin/config/cloudflare-preview/`
    - `POST /api/v1/portal/admin/config/cloudflare-toggle/`
  - ativacao/desativacao em 1 clique com atualizacao automatica de URLs dos frontends/API, CORS e rollback de snapshot local.
- Portal CMS runtime cloud (`T6.3.2-A10`):
  - novo endpoint admin `POST /api/v1/portal/admin/config/cloudflare-runtime/` com acoes `start|stop|status`.
  - runtime do tunnel persiste PID/log em `.runtime/ops` e retorna ultimas linhas de log para o painel.
  - monitoramento de servicos do ecossistema passou a incluir `cloudflare` em `GET /api/v1/orders/ops/realtime/`.
- Portal CMS cloud dev (`T6.3.2-A11`):
  - `cloudflare_settings` evoluiu com `dev_mode` e `dev_urls` para habilitar dominios aleatorios `trycloudflare.com` no modo de desenvolvimento.
  - `cloudflare-runtime start` em `dev_mode` inicia tunnels por servico (`portal/client/admin/api`), captura URLs publicas por log e sincroniza automaticamente a configuracao quando `auto_apply_routes` estiver ativo.
  - desativacao (`cloudflare-toggle enabled=false`) encerra tunnel principal e tunnels dev, limpando URLs temporarias.
- Automacao terminal cloud (`T6.3.2-A12`):
  - script `scripts/cloudflare_admin.sh` publicado para controlar status/toggle/runtime de Cloudflare DEV/PROD via terminal usando a API admin.
  - script `scripts/cloudflare_sync_frontends.sh` publicado para sincronizar `.env.local` de `admin/client/portal` com a URL atual da API (incluindo rotacao `trycloudflare`).
  - `start_admin_dev.sh` e `start_client_dev.sh` passaram a respeitar `NEXT_PUBLIC_API_BASE_URL` de `.env.local` antes do fallback local.
- Observabilidade cloud dev (`T6.3.2-A13`):
  - runtime Cloudflare DEV passou a incluir monitoramento de conectividade por servico (status, HTTP, latencia, URL checada e timestamp).
  - acao `refresh` adicionada no endpoint de runtime para regenerar dominios aleatorios com um clique.
  - Web Admin passou a exibir painel de monitoramento por dominio e botao `Gerar novos dominios DEV`.
- Hardening cloud dev (`T6.3.2-A14`):
  - status do runtime passou a sincronizar rotacao de `dev_urls` diretamente no `PortalConfig`, garantindo reconfiguracao automatica dos endpoints quando dominio aleatorio mudar.
  - backend `dev` passou a aceitar `*.trycloudflare.com` em `ALLOWED_HOSTS`.
  - script `scripts/install_cloudflared_local.sh` publicado para setup local do binario.
  - hotfix `T6.3.2-A14-HF3` aplicado: parser de URL dos logs dev endurecido para ignorar `api.trycloudflare.com`, auto-apply parcial de rotas por servico e CORS regex para `https://*.trycloudflare.com`.
- Financas pessoais (`T8.1.1`):
  - novo app `personal_finance` com `accounts`, `categories`, `entries` e `budgets`.
  - ownership estrito por usuario em querysets e validacoes.
  - API dedicada em `/api/v1/personal-finance/...`.
- Financas pessoais (`T8.1.2`):
  - endpoint de exportacao de dados pessoais em `/api/v1/personal-finance/export/`.
  - trilha de auditoria por evento em `PersonalAuditLog`.
  - retencao operacional via comando `purge_personal_audit_logs`.
- Financas pessoais (`T8.2.1`):
  - discovery de evolucao concluido com priorizacao de recorrencia, resumo mensal e importacao CSV MVP.
- Financas pessoais (`T8.2.2`):
  - recorrencia com materializacao idempotente (`/recurring-rules/materialize/`).
  - resumo mensal por competencia com totais e status de budgets (`/summary/monthly/`).
  - importacao CSV com preview/confirmacao e deduplicacao por hash (`/imports/preview/` e `/imports/<id>/confirm/`).

### Web Portal (Next.js - 3000)
- Status: institucional em evolucao de template (`classic` + `letsfit-clean`).
- Integracao: cardapio por API (`/today/` e `/by-date/`).
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A2`): consumo de `active_template` do CMS em runtime (server-side).
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A2-HF1`): fallback automatico de API no cardapio para host atual (`:8000`) quando variavel de ambiente nao estiver definida.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A3`): template LetsFit passou a consumir secoes dinamicas do CMS (`hero`, `benefits`, `categories`, `kit`, `how_to_heat`, `faq`) incluindo fotos/links via `body_json`.
- Atualizacao concluida em 26/02/2026 (`T7.2.3-HF2`): links de Area do Cliente/Admin parametrizados por env e fallback local em desenvolvimento (`3001/3002`) para facilitar fluxo iniciado em `localhost:3000`.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A6`): pagina `/app` passou a consumir release mobile publicada via CMS e rota dinamica `/app/downloads/[target]` foi adicionada para redirecionar Android/iOS.
- Risco de conflito: alto em paralelo com trilha Antigravity de template.

### Web Client (Next.js - 3001)
- Status: auth real concluida (`register/token/refresh/me`).
- Pedido/historico: escopo autenticado sem demo.
- Checkout online concluido com intents por metodo (PIX/CARD/VR), painel de instrucoes e polling via `intent/latest`.
- Metodos de pagamento agora habilitados dinamicamente pelo payload publico `payment_providers` do Portal CMS.
- Atualizacao concluida em 26/02/2026 (`T7.2.3-HF1`): fallback automatico de API para host atual (`:8000`) e mensagem de erro de rede padronizada.
- Atualizacao concluida em 26/02/2026 (`T7.2.3-HF2`): jornada UX de ponta a ponta (login -> cardapio -> checkout -> pedidos -> confirmacao de recebimento), com indicador de conectividade API, guard de autenticacao no checkout e suporte validado para execucao em `localhost:3000` (`CLIENT_PORT=3000`).
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A4`): modo de template dinamico integrado ao CMS (`channel=client`) com dois temas (`client-classic` e `client-quentinhas`) no layout, header, footer e jornada do cardapio.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A7`): novo template `client-vitrine-fit` (grid mais densa e foco em fotos de pratos), bloco de login social Google/Apple na Conta e callbacks web para recebimento do `code`.
- Atualizacao concluida em 27/02/2026 (`T9.2.1-A2-HF4`): rota `/conta/confirmar-email` adicionada para validar token de confirmacao, com status de e-mail verificado e reenvio de confirmacao na area autenticada.

### Admin Web (Next.js - 3002)
- Status: `T9.1.2` concluida (relatorios/exportacoes + UX/IX modular).
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF1`): correcoes de `onChange` para evitar crash client-side no login e ajuste de `allowedDevOrigins` no Next 16 para acesso em `10.211.55.21:3002`.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF2`): liberacao de CORS do backend para origem `:3002`, fallback automatico da API no Admin Web e exibicao de erros diretamente no card de login.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF3`): padronizacao visual global com cores de status (success/warning/danger/info) e aplicacao da logo oficial (PNG original) no Admin Web, Portal e Client.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF4`): rotas diretas `/modulos` e `/prioridades` com redirect para `/#modulos` e `/#prioridades`, evitando erro 404 em acesso por URL/bookmark (substituido pela navegacao por hotpages).
- Entrega atual: modulos de Pedidos/Financeiro/Estoque/Cardapio/Compras/Producao e Usuarios/RBAC estaveis, com hotpages, menus contextuais, graficos e relatorios/exportacoes CSV com filtros por periodo.
- Atualizacao concluida em 25/02/2026 (`T9.1.2`): exportacoes por modulo (Pedidos/Compras/Producao/Financeiro), traducao pt-BR de status operacionais e consolidacao do modulo de Relatorios como ativo.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A1`): modulo `Portal CMS` no Admin Web para selecionar template ativo existente e publicar configuracao de portal.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A4`): `Portal CMS` passou a configurar template ativo do Web Cliente (`client_active_template`) e disponibilizar edicao de conteudo para templates de portal e cliente.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A5`): `Portal CMS` passou a ter area de conectividade para configurar dominio/subdominios e URLs de Portal/Client/Admin/API/Proxy em ambiente dev local (`host mrquentinha`) com lista de origens CORS.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A6`): `Portal CMS` ganhou secao `Build mobile` com criacao/compilacao/publicacao de releases e acompanhamento de status.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A2`): Portal Web passou a consumir `active_template` do CMS em runtime (server-side), refletindo mudancas do Admin sem rebuild por variavel de ambiente.
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A7`): `Portal CMS` ganhou secao `Autenticacao social` para configurar Google/Apple (web + iOS + Android) com persistencia centralizada em `auth_providers`.
- Atualizacao concluida em 27/02/2026 (`T6.3.2-A9`): `Portal CMS` ganhou secao `Cloudflare online (1 clique)` para preview e ativacao/desativacao de exposicao na internet com modos `local_only`, `cloudflare_only` e `hybrid`.
- Atualizacao concluida em 27/02/2026 (`T6.3.2-A10`): secao Cloudflare ganhou controle de runtime do tunnel (`start/stop/status`) e exibicao das ultimas linhas de log em tela.
- Atualizacao concluida em 27/02/2026 (`T6.3.2-A11`): secao Cloudflare ganhou modo DEV com dominios aleatorios (`trycloudflare`), campos de dominio/tunnel condicionais e exibicao das URLs publicas por servico no runtime.
- Atualizacao concluida em 27/02/2026 (`T6.3.2-A12`): automacao terminal para Cloudflare DEV/PROD e sincronizacao dos endpoints de API dos frontends via scripts oficiais.
- Atualizacao concluida em 27/02/2026 (`T6.3.2-A13`): monitoramento de conectividade dos dominios DEV e acao `refresh` para gerar novos dominios aleatorios no painel Cloudflare.
- Atualizacao concluida em 26/02/2026 (`T7.2.4-A1`): `Portal CMS` ganhou secao `Pagamentos` para configurar Mercado Pago/Efi/Asaas, ordem por metodo (PIX/CARD/VR), recebedor CPF/CNPJ e teste de conexao por provider.
- Atualizacao concluida em 26/02/2026 (`T7.2.4-A2`): `Portal CMS` passou a selecionar provider unico por canal (`Web Cliente` e `App Mobile`) com campos adaptativos por provider.
- Atualizacao concluida em 26/02/2026 (`T7.2.4-A3`): dashboard recebeu monitoramento realtime de servicos/pagamentos e novo modulo `/modulos/monitoramento` com visao de saude e lifecycle.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A1`): Cardapio ganhou secao de composicao (ingredientes + prato com receita) para viabilizar ciclo completo de operacao.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A2`): Compras ganhou registro operacional de compra com itens (entrada em estoque), alem da geracao de requisicao por cardapio com seletor.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A3`): Cardapio ganhou padrao de periodos (Manha/Cafe, Almoco, Jantar, Lanche) para organizacao de menus diarios.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A4`): modulo Cardapio finalizado com edicao de insumos/pratos e composicao completa no Admin.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A5`): fotos dinamicas de pratos e insumos sincronizadas no banco e expostas no endpoint de cardapio (incluindo composicao com `image_url` por insumo).
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A6`): compras/OCR com captura/upload de imagens no Admin, persistencia de fotos no destino apos OCR aplicado e icones visuais por item/comprovante.
- Atualizacao concluida em 26/02/2026 (`T9.1.3-A7`): ciclo operacional completo no Admin com linha de producao (dashboard realtime, auto-checagem de estoque no cardapio, alertas de compras, entrega e confirmacao de recebimento pelo cliente).
- Atualizacao concluida em 26/02/2026 (`T6.3.2-A3`): modulo Portal CMS ganhou editor de secoes dinamicas (template/pagina/body_json) e a composicao ganhou upload de fotos para insumos e pratos.
- Atualizacao concluida em 27/02/2026 (`T9.2.6-A1`): nova area `/perfil` no Web Admin (todos os templates) para administracao completa do usuario logado com dados adicionais, endereco, documentos, foto de perfil, digitalizacao por camera, biometria por foto e logoff.
- Atualizacao concluida em 27/02/2026 (`T9.2.6-A2`): camada global de validacao/formatacao de formularios aplicada no Admin/Client/Portal (CPF/CNPJ/CEP/email/senha/datas) com reforco de validacao backend para senha de cadastro e recebedor de pagamentos.
- Atualizacao concluida em 27/02/2026 (`T9.2.1-A2-HF4`): modulo `/modulos/usuarios-rbac` passou a exibir status de validacao de e-mail e pendencias de dados essenciais para habilitacao de pagamento/autenticacao por usuario.
- Workspace ativo: `workspaces/web/admin`.
- Hotfix `T6.3.2-A14-HF1` implementado: resolucao automatica de `api_base_url` em runtime aplicada nos frontends `admin/client/portal` para acessos via dominios dinamicos `trycloudflare`.
- Status de validacao externa do fluxo Cloudflare DEV: concluido em `27/02/2026 15:04` (Portal/Client/Admin/API online, health 200, comunicacao frontend <-> API validada no teste funcional).
- Hotfix `T6.3.2-A14-HF2` implementado: em acesso local por IP/localhost, os frontends passaram a resolver `api_base_url` para `http://<host-local>:8000`, evitando dependencia de dominio Cloudflare para operar no modo DEV local.
- Hotfix `T6.3.2-A14-HF2` implementado: Portal (`Header/Footer/Home`) ajustado para links locais dinamicos sem mismatch de hidratacao.
- Proximo alvo tecnico: executar `T8.2.3` (hardening pos-MVP da trilha pessoal).
- Proximo alvo operacional: executar `T9.2.1-A2` (rodada manual E2E completa) e manter `T8.2.3` como trilha tecnica de backend.

## Portas e scripts oficiais
- Backend: `8000` -> `scripts/start_backend_dev.sh`
- Portal: `3000` -> `scripts/start_portal_dev.sh`
- Client: `3001` -> `scripts/start_client_dev.sh`
- Admin Web: `3002` -> `scripts/start_admin_dev.sh`
- Proxy local Nginx: `8088` -> `scripts/start_proxy_dev.sh`
- Smoke: `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh`, `scripts/smoke_proxy_dev.sh`
- Seed: `scripts/seed_demo.sh`
- Quality gate: `scripts/quality_gate_all.sh`
- Sync docs: `scripts/sync_memory.sh --check`

## Endpoints chave
- `GET /`
- `GET /api/v1/health`
- `POST /api/v1/accounts/register/`
- `POST /api/v1/accounts/token/`
- `POST /api/v1/accounts/token/refresh/`
- `GET /api/v1/accounts/me/`
- `GET /api/v1/accounts/me/profile/`
- `PATCH /api/v1/accounts/me/profile/`
- `GET /api/v1/accounts/email-verification/confirm/?token=<token>`
- `POST /api/v1/accounts/email-verification/resend/`
- `GET /api/v1/accounts/roles/`
- `GET /api/v1/accounts/users/`
- `GET /api/v1/accounts/users/<id>/`
- `POST /api/v1/accounts/users/<id>/roles/`
- Publicos read-only de menu:
  - `GET /api/v1/catalog/menus/by-date/<YYYY-MM-DD>/`
  - `GET /api/v1/catalog/menus/today/`
- Pagamentos intent:
  - `POST /api/v1/orders/payments/<id>/intent/`
  - `GET /api/v1/orders/payments/<id>/intent/latest/`
- Webhook pagamentos:
  - `POST /api/v1/orders/payments/webhook/` (`X-Webhook-Token`)
  - `POST /api/v1/orders/payments/webhook/mercadopago/` (`X-Webhook-Token`)
  - `POST /api/v1/orders/payments/webhook/asaas/` (`X-Webhook-Token`)
  - `POST /api/v1/orders/payments/webhook/efi/` (`X-Webhook-Token`)
- Portal CMS publico:
  - `GET /api/v1/portal/config/`
  - `GET /api/v1/portal/config/version`
  - `GET /api/v1/portal/mobile/releases/latest/`
- Portal CMS admin (config):
  - `GET/POST /api/v1/portal/admin/config/`
  - `PATCH /api/v1/portal/admin/config/<id>/`
  - `POST /api/v1/portal/admin/config/<id>/publish/`
  - `POST /api/v1/portal/admin/config/test-payment-provider/`
  - `POST /api/v1/portal/admin/config/cloudflare-preview/`
  - `POST /api/v1/portal/admin/config/cloudflare-toggle/`
  - `POST /api/v1/portal/admin/config/cloudflare-runtime/`
- Financas pessoais:
  - `GET/POST /api/v1/personal-finance/accounts/`
  - `GET/POST /api/v1/personal-finance/categories/`
  - `GET/POST /api/v1/personal-finance/entries/`
  - `GET/POST /api/v1/personal-finance/recurring-rules/`
  - `POST /api/v1/personal-finance/recurring-rules/materialize/`
  - `GET/POST /api/v1/personal-finance/budgets/`
  - `GET /api/v1/personal-finance/summary/monthly/?month=YYYY-MM`
  - `POST /api/v1/personal-finance/imports/preview/`
  - `POST /api/v1/personal-finance/imports/<id>/confirm/`
  - `GET /api/v1/personal-finance/imports/`
  - `GET /api/v1/personal-finance/export/`
  - `GET /api/v1/personal-finance/audit-logs/`
- Portal CMS admin (release mobile):
  - `GET/POST /api/v1/portal/admin/mobile/releases/`
  - `POST /api/v1/portal/admin/mobile/releases/<id>/compile/`
  - `POST /api/v1/portal/admin/mobile/releases/<id>/publish/`

## Plano da etapa ativa
- Trilha principal: `9.1 Admin Web completo` (concluida).
- T9.0.1 concluida (Admin Web foundation: shell + auth + dashboard inicial).
- T9.0.2 concluida (Admin Web operacional: Pedidos, Financeiro e Estoque conectados ao backend).
- T9.0.3 concluida (Admin Web expansion: baseline de Cardapio, Compras e Producao).
- T9.1.1 concluida (modulo Usuarios/RBAC entregue com endpoints admin + painel no Admin Web).
- T9.1.1-HF1 concluida (hotfix de login no Admin Web: crash client-side ao digitar usuario + ajuste de allowedDevOrigins para acesso via IP).
- T9.1.1-HF2 concluida (hotfix de login no Admin Web: CORS backend para `:3002` + fallback de API base + feedback inline de erro no formulario).
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF3`): padronizacao visual global com cores de status (success/warning/danger/info) e aplicacao da logo oficial (PNG original) no Admin Web, Portal e Client.
- Hotfix aplicado em 25/02/2026 (`T9.1.1-HF4`): rotas diretas `/modulos` e `/prioridades` no Admin Web agora redirecionam para `/#modulos` e `/#prioridades`, evitando erro 404 em acesso por URL/bookmark.
- T9.1.2 concluida (relatorios/exportacoes no Admin Web com filtro por periodo e exportacao CSV funcional por modulo).
- T6.3.2-A6 concluida (release mobile no Portal CMS com publicacao de links para QR/download no Portal).
- T6.3.2-A7 concluida (template cliente `client-vitrine-fit` + parametros OAuth Google/Apple gerenciados no Portal CMS).
- T6.3.2-A9 concluida (Cloudflare online no Portal CMS com preview/toggle e coexistencia local+internet por modo `hybrid`).
- T6.3.2-A10 concluida (runtime do cloudflared no Admin + monitoramento realtime do servico `cloudflare`).
- T6.3.2-A11 concluida (modo DEV Cloudflare com dominios aleatorios por servico + sincronizacao automatica de URLs no backend).
- T6.3.2-A12 concluida (operacao Cloudflare via terminal + sync de `.env.local` dos frontends quando endpoints mudam).
- T6.3.2-A13 concluida (monitoramento de conectividade por dominio DEV + botao de regeneracao de dominios aleatorios).
- T7.2.4-A1 concluida (multigateway no Portal CMS + webhooks dedicados por provider + habilitacao dinamica de metodos no web client).
- T8.0.1 concluida (discovery de financas pessoais + ADR de segregacao entre dominio operacional e pessoal).
- T8.1.1 concluida (backend `personal_finance` com isolamento por ownership + testes API).
- T8.1.2 concluida (LGPD operacional com exportacao, auditoria e retencao de logs).
- T8.2.1 concluida (discovery da evolucao funcional da trilha pessoal).
- T8.2.2 concluida (recorrencia, resumo mensal e importacao CSV MVP em producao de desenvolvimento).
- T9.2.6-A1 concluida (area de perfil completo do usuario logado no Admin Web + endpoint autenticado `me/profile` com suporte a upload de arquivos).
- T9.2.6-A2 concluida (validadores/formatadores globais de formularios no ecossistema web + hardening de validacao de senha/email/documento).
- Proxima subetapa unica: executar `T7.2.4-A4` (homologacao externa dos tres gateways com credenciais reais, assinatura de webhook por provider e validacao fim a fim de webhook/status).
- Trilhas correlatas apos 9.1: `T6.2.1` (Antigravity), `T8.2.3` (hardening backend) e `T9.2.1` (qualidade operacional manual).
