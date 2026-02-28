# Plano do MVP e cronograma

Data de referencia: 28/02/2026.

## Status atual do roadmap
- Etapa 0: concluida
- Etapa 1: concluida
- Etapa 2: concluida
- Etapa 3 e 3.1: concluida
- Etapa 4: concluida
- Etapa 5.0 a 5.6.3: concluida
- Etapa 6.0, 6.0.1 e 6.1.1: concluida
- Etapa 6.3.1: concluida
- Etapa 6.3.2 (A1 ate A7 + A9): concluida
- Etapa 7.0: concluida
- Etapa 7.1 (7.1.1 a 7.1.3): concluida em 25/02/2026
- Etapa 7.2 (T7.2.1 a T7.2.3): concluida em 26/02/2026
- Etapa 7.2.4-A1 (multigateway em tempo real): concluida em 26/02/2026
- Etapa 7.2.4-A2 (roteamento por canal frontend + campos adaptativos): concluida em 26/02/2026
- Etapa 7.2.4-A3 (monitoramento realtime de gateways/ecossistema): concluida em 26/02/2026
- Etapa 8.0.1 (discovery): concluida em 26/02/2026
- Etapa 8.1.1 (MVP tecnico backend): concluida em 26/02/2026
- Etapa 8.1.2 (LGPD operacional backend): concluida em 26/02/2026
- Etapa 8.2.1 (discovery de evolucao): concluida em 26/02/2026
- Etapa 8.2.2 (implementacao evolucao MVP): concluida em 26/02/2026
- Etapa 9.0 e 9.1 (ate T9.1.3-A7): concluida em 26/02/2026
- Etapa 9.2.1 (plano de testes manuais E2E): planejamento concluido em 26/02/2026
- Etapa 9.2.3 (templates e UX do Web Admin): concluida em 26/02/2026
- Etapa 9.2.5 (template AdminDek e refinacao visual do Web Admin): concluida em 26/02/2026
- Etapa 9.2.6-A1 (perfil completo do usuario logado no Web Admin): concluida em 27/02/2026
- Etapa 9.2.6-A2 (validadores/formatadores globais de formularios no ecossistema web): concluida em 27/02/2026
- Etapa 9.2.7-A1 (gestao de clientes no Web Admin + compliance LGPD/KYC): concluida em 27/02/2026
- Etapa 9.2.7-A2 (novo modulo Administracao do servidor e reorganizacao do Portal CMS): concluida em 27/02/2026
- Etapa 9.2.7-A3 (assistente de instalacao/deploy com workflow continuo do instalador): concluida em 28/02/2026
- Etapa 9.2.8-A1 (modulo independente `Instalacao / Deploy` + pre-requisitos de producao no wizard): concluida em 28/02/2026
- Etapa 6.3.2-A9 (exposicao online Cloudflare com toggle 1 clique no Portal CMS): concluida em 27/02/2026
- Etapa 6.3.2-A10 (runtime cloudflared + monitoramento realtime do tunnel): concluida em 27/02/2026
- Etapa 6.3.2-A11 (modo DEV Cloudflare com dominios aleatorios trycloudflare): concluida em 27/02/2026
- Etapa 6.3.2-A12 (automacao por terminal + sync de endpoints frontend): concluida em 27/02/2026
- Etapa 6.3.2-A13 (monitoramento de conectividade DEV + refresh de dominios): concluida em 27/02/2026
- Etapa 6.3.2-A14 (hardening da rotacao DEV + ALLOWED_HOSTS trycloudflare): concluida em 27/02/2026

## Fechamento do MVP operacional
O MVP operacional foi fechado com o backend cobrindo:
- catalogo
- estoque e compras
- producao
- pedidos
- financeiro completo no escopo MVP (AP/AR/caixa/ledger/conciliacao/fechamento/relatorios)

## Cronograma consolidado (realizado)
- Fase base: Etapas 0 a 2
- Fase operacao: Etapas 3, 3.1 e 4
- Fase financeira: Etapa 5 (5.0 a 5.6.3)
- Fase canais web iniciais: Etapa 6.0/6.0.1/6.1.1, 6.3.1 e 7.0
- Fase auth/rbac cliente real: Etapa 7.1
- Fase pagamentos online: Etapa 7.2
- Fase pagamentos online avancados: `T7.2.4-A1` (configuracao centralizada de gateways no Portal CMS + webhooks por provider)
- Fase pagamentos online avancados (continuidade): `T7.2.4-A2` e `T7.2.4-A3` (provider por canal frontend + monitoramento realtime no backend/admin)
- Fase financas pessoais (fundacao): Etapas 8.0.1, 8.1.1 e 8.1.2
- Fase financas pessoais (evolucao): Etapas 8.2.1 (discovery) e 8.2.2 (implementacao MVP)
- Fase operacao interna web: Etapas 9.0 e 9.1
- Fechamento da trilha CMS em canais web: `T6.3.2-A1` ate `T6.3.2-A7` + `T6.3.2-A9`
- Fase de qualidade operacional: `T9.2.1` (plano e campanha recorrente de testes manuais E2E)
- Fase de governanca de identidade no Admin Web: `T9.2.6-A1` (cadastro completo de perfil, documentos e biometria por foto do usuario logado)
- Fase de qualidade de dados em formularios: `T9.2.6-A2` (formatacao e validacao global para CPF/CNPJ/CEP/email/senha/datas nos frontends web + reforco backend)
- Fase de governanca de clientes no ecommerce: `T9.2.7-A1` (modulo administrativo de clientes com status de conta, KYC, consentimentos e solicitacoes LGPD)
- Fase de governanca operacional de infraestrutura no Admin Web: `T9.2.7-A2` (modulo dedicado para e-mail, conectividade/dominio e build/release)
- Fase de governanca operacional de infraestrutura no Admin Web (evolucao): `T9.2.7-A3` (wizard de instalacao/deploy + guard rail de atualizacao continua do instalador)
- Fase de instalacao/deploy dedicada: `T9.2.8-A1` (novo modulo `Instalacao / Deploy` com validacao de pre-requisitos de DNS/servidor e gateway de pagamento).
- Fase de conectividade DEV online: `T6.3.2-A11` (Cloudflare em modo desenvolvimento com URLs aleatorias por servico e sem dependencia de dominio real)
- Fase de automacao operacional cloud: `T6.3.2-A12` (scripts de terminal para operar Cloudflare DEV/PROD e sincronizar URLs de API dos frontends)
- Fase de observabilidade cloud em DEV: `T6.3.2-A13` (monitoramento de conectividade por servico e refresh de dominios aleatorios no Web Admin)
- Fase de hardening cloud em DEV: `T6.3.2-A14` (sincronizacao automatica de rotacao de dominios no status e suporte de host no backend)

## Proximas fases (planejado)
### 6.2 Consolidacao visual do portal (ownership Antigravity)
Dependencias:
- estabilizacao de lock de trilha visual no fluxo paralelo
- validacao final de UX/responsividade dos templates publicados
- smoke completo com CMS ativo no template final

### 8 Financas pessoais (expansao de produto)
Dependencias:
- operacao B2C estabilizada
- governanca de dados pessoais e segregacao de escopos
- definicao de produto e limites entre financeiro operacional e pessoal

### 9.2 Qualidade operacional por testes manuais E2E
Dependencias:
- ambiente local padronizado com backend/portal/client/admin estaveis
- seed idempotente executada para garantir massa de dados representativa
- checklist unificado publicado em `docs/memory/PLANO_T9_2_1_TESTES_MANUAIS_E2E.md`

### 7.2.4 Pagamentos multigateway (Mercado Pago, Efi e Asaas)
Dependencias:
- credenciais de homologacao/producao de cada provider cadastradas no Portal CMS
- webhook publico com token valido e conectividade externa para callback
- validacao fim a fim no client web e no app mobile com polling/status em tempo real

## Passo atual do cronograma
- Etapa ativa recomendada: `T7.2.4-A4` (homologacao real dos gateways Mercado Pago/Efi/Asaas com credenciais oficiais, assinatura de webhook por provider e validacao externa).
- Trilha de qualidade paralela: `T9.2.1-A2` (rodada manual E2E completa do ecossistema, incluindo matrix de pagamentos por provider).
- Trilha tecnica paralela: `T8.2.3` (hardening pos-MVP de financas pessoais).
- Trilha de experiencia operacional: `T9.2.3` concluida com template `admin-adminkit` e fluxo guiado do ciclo operacional no Web Admin.
- Resultado do passo anterior: `T7.2.4-A2` e `T7.2.4-A3` concluidas em 26/02/2026 com provider unico por canal (`web/mobile`), campos adaptativos por provider no Admin e monitoramento realtime em `/api/v1/orders/ops/realtime/` + modulo `/modulos/monitoramento`.
- Resultado complementar mais recente: `T9.2.6-A1` concluida em 27/02/2026 com nova area `/perfil` no Web Admin (todos os templates), endpoint `GET/PATCH /api/v1/accounts/me/profile/` e suporte a upload/digitalizacao de foto/documentos/biometria.
- Resultado complementar atual: `T6.3.2-A9` concluida em 27/02/2026 com area `Cloudflare online (1 clique)` em `/modulos/portal`, endpoints de preview/toggle e suporte a modos `local_only/cloudflare_only/hybrid` para coexistencia local + internet.
- Resultado complementar mais recente: `T6.3.2-A10` concluida em 27/02/2026 com acao runtime (`start/stop/status`) do tunnel via Admin, script operacional `scripts/cloudflare_tunnel.sh` e visibilidade do servico `cloudflare` no monitoramento realtime.
- Resultado complementar mais recente: `T6.3.2-A11` concluida em 27/02/2026 com `dev_mode` no Cloudflare para gerar dominios aleatorios (`trycloudflare`) em DEV, com sincronizacao automatica das URLs no backend e exibicao por servico no Web Admin.
- Resultado complementar mais recente: `T6.3.2-A12` concluida em 27/02/2026 com automacao terminal (`cloudflare_admin.sh`) para os mesmos fluxos do Web Admin e sincronizacao de `.env.local` dos frontends quando as URLs mudam.
- Resultado complementar mais recente: `T6.3.2-A13` concluida em 27/02/2026 com botao `Gerar novos dominios DEV` e monitoramento ativo de conectividade/latencia/HTTP por dominio aleatorio no runtime do Web Admin.
- Resultado complementar mais recente: `T6.3.2-A14` concluida em 27/02/2026 com sincronizacao automatica de URLs rotacionadas no `status` e eliminacao de `DisallowedHost` para `*.trycloudflare.com` no ambiente dev.
- Hotfix `T6.3.2-A14-HF1` implementado em 27/02/2026 (frontend -> API em dominios dinamicos Cloudflare): resolucao automatica de `api_base_url` em runtime concluida para `portal/client/admin`; validacao externa ficou pendente porque os dominios informados retornaram `Cloudflare 530 (Error 1033)` no momento do teste.
- Hotfix `T6.3.2-A14-HF2` implementado em 27/02/2026 (prioridade rede local): frontends em acesso local (`10.x/localhost`) passaram a usar API local `http://<host>:8000` em runtime e o Portal teve ajuste de links dinamicos sem mismatch de hidratacao.
- Resultado complementar mais recente: `T9.2.7-A1` concluida em 27/02/2026 com novo modulo `/modulos/clientes`, API administrativa de ciclo de vida do cliente e integracao de elegibilidade de checkout no backend.

## Regra de execucao continua
Cada nova fase deve manter:
- cobertura de testes automatizados
- idempotencia em integracoes criticas
- documentacao viva (`CHANGELOG`, `DECISIONS`, runbooks)
