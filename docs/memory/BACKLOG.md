# Backlog Priorizado (P0/P1/P2)

Referencia: 27/02/2026.

## Regras de execucao
- Branch policy:
  - Codex: `main` e `main-etapa-*`
  - Antigravity: `AntigravityIDE` e `AntigravityIDE/etapa-*`
  - Union: `Antigravity_Codex`
- Prefixo de IDs:
  - `T7.*` pagamentos/client
  - `T6.*` portal/cms/infra
  - `T9.*` admin web gestao
  - `T8.*` financas pessoais

## Concluidas recentes
- [x] `T7.2.1` payment intents com idempotencia.
- [x] `T7.2.2` webhook de pagamento + reconciliacao `AR/Cash/Ledger`.
- [x] `T7.2.3` checkout online no client com intents por metodo e polling de status.
- [x] `T7.2.4-A1` multigateway no Portal CMS (Mercado Pago/Efi/Asaas) com roteamento por metodo, recebedor CPF/CNPJ, teste de conexao e webhooks por provider.
- [x] `T7.2.4-A2` provider unico por frontend (`web` e `mobile`) com roteamento por canal na criacao de intent e campos adaptativos no Admin.
- [x] `T7.2.4-A3` monitoramento realtime do ecossistema/pagamentos no backend e Admin (`/api/v1/orders/ops/realtime/` + `/modulos/monitoramento`).
- [x] `T6.3.1` Portal CMS backend-only (Config/Sections + API publica/admin).
- [x] `T6.3.2-A6` release mobile no Portal CMS (backend/admin/portal + endpoint publico latest).
- [x] `T6.3.2-A7` template `client-vitrine-fit` + configuracao OAuth Google/Apple (web/mobile) centralizada no Portal CMS.
- [x] `T6.3.2-A9` exposicao online via Cloudflare no Portal CMS com preview e toggle (1 clique), URLs/CORS automaticos e modo `hybrid` para coexistencia local+internet.
- [x] `T6.3.2-A10` runtime do tunnel Cloudflare com `start/stop/status` via Admin + monitoramento do servico no realtime do ecossistema.
- [x] `T9.0.1` Admin Web foundation (shell + auth + dashboard inicial).
- [x] `T9.0.2` Admin Web operacional (Pedidos, Financeiro, Estoque).
- [x] `T9.2.6-A1` perfil completo do usuario logado no Web Admin com endpoint `me/profile` e upload de foto/documentos/biometria.
- [x] `T9.2.6-A2` validadores/formatadores globais de formularios (CPF/CNPJ/CEP/email/senha/datas) no Admin/Client/Portal, com reforco de validacao no backend.
- [x] `T8.0.1` discovery de financas pessoais com segregacao LGPD (docs + ADR).
- [x] `T8.1.1` MVP tecnico backend de financas pessoais (`personal_finance`) com isolamento por ownership e testes.
- [x] `T8.1.2` camada operacional LGPD (exportacao de dados pessoais + auditoria + retencao de logs).
- [x] `T8.2.1` discovery da evolucao da trilha pessoal (recorrencia, resumo mensal e importacao CSV MVP).
- [x] `T8.2.2` implementacao da evolucao MVP da trilha pessoal (recorrencia, resumo mensal e importacao CSV preview/confirm).

## P0 (critico - receita/operacao)

### T6.3.1 (CONCLUIDA)
- Objetivo: Portal CMS backend-only (Config + Sections + API publica/admin).
- Status: concluida em 25/02/2026.
- Escopo: backend + docs.
- Conflito Codex x Antigravity: medio (intersecao funcional com portal 6.2).
- Branch sugerida: `main-etapa-6.3-PortalCMS-BackendOnly`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.0.1 (CONCLUIDA)
- Objetivo: Admin Web foundation (auth shell + dashboard inicial).
- Status: concluida em 25/02/2026.
- Escopo: admin web novo workspace.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-9.0-AdminWeb-Foundation`.
- DoD:
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/sync_memory.sh --check`

### T9.0.2 (CONCLUIDA)
- Objetivo: Admin Web MVP operacional (Pedidos, Financeiro, Estoque).
- Status: concluida em 25/02/2026.
- Escopo: admin + backend.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-9.0-AdminWeb-CoreOps`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/smoke_stack_dev.sh`
  - `bash scripts/sync_memory.sh --check`

### T9.0.3 (CONCLUIDA)
- Objetivo: expandir o Admin com dashboard consolidado e baseline de Cardapio/Compras/Producao.
- Status: concluida em 26/02/2026.
- Escopo: admin + backend.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-9.0-AdminWeb-Expansion`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && make test`
  - `source ~/.nvm/nvm.sh && nvm use --lts`
  - `cd workspaces/web/admin && npm run lint && npm run build`
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

## P1 (escala/UX)

### T6.2.1 (P1)
- Objetivo: consolidar template `letsfit-clean` no portal.
- Escopo: portal + ui.
- Conflito Codex x Antigravity: alto (ownership Antigravity).
- Branch sugerida:
  - Antigravity: `AntigravityIDE/etapa-6.2-PortalTemplateLetsFit`
  - Codex: somente suporte de integracao via `Antigravity_Codex` quando liberado.

### T6.3.2 (P1)
- Objetivo: integrar CMS em portal/client (render por template/page + parametros de autenticacao social).
- Escopo: portal + backend.
- Conflito Codex x Antigravity: alto.
- Branch sugerida: `main-etapa-6.3-PortalCMS-Integracao`.
- Status parcial: `A1..A7` e `A9` concluidas; pendente `A8` para troca de `code` OAuth no backend.

### T7.2.4 (P1)
- Objetivo: evoluir pagamentos para operacao multigateway real-time (Mercado Pago, Efi, Asaas) com governanca de credenciais no Admin Web.
- Escopo: backend + admin + web client + mobile contract + docs.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-7.2-Pagamentos-Multigateway`.
- Status:
  - `A1` concluida: configuracao centralizada + webhooks dedicados + client consumindo metodos dinamicos.
  - `A2` concluida: provider por canal (`web/mobile`) com selecao unica e roteamento por header.
  - `A3` concluida: observabilidade realtime por provider com dashboard, modulo de monitoramento e serie de eventos.
  - `A4` pendente: homologacao externa das tres APIs, assinatura webhook por provider e validacao de callback real em ambiente publico.

### T9.1.1 (P1)
- Objetivo: Admin Web completo (modulos 1..10 do epico de gestao).
- Escopo: admin + backend + relatorios.
- Conflito Codex x Antigravity: medio/alto.
- Branch sugerida: `main-etapa-9.1-AdminWeb-Completo`.

### T9.1.2 (P1)
- Objetivo: exportacoes CSV/Excel e graficos no Admin.
- Escopo: admin + API relatorios.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-9.1-AdminWeb-Relatorios`.

### T9.2.1 (P1)
- Objetivo: campanha recorrente de testes manuais E2E cobrindo todos os recursos da aplicacao.
- Escopo: QA manual + memoria operacional + plano de correcao por rodada.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-9.2-TestesManuais-E2E`.
- Evidencia de plano: `docs/memory/PLANO_T9_2_1_TESTES_MANUAIS_E2E.md`.

## P2 (roadmap e hardening)

### T6.1.1 (P2)
- Objetivo: Nginx/proxy local (www/admin/api/app) com runbook de operacao.
- Escopo: infra + docs.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-6.1-NginxLocal`.

### T8.0.1 (CONCLUIDA)
- Objetivo: discovery de financas pessoais com segregacao LGPD.
- Status: concluida em 26/02/2026 (docs-first).
- Escopo: docs + arquitetura + backlog.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-8.0-FinancasPessoais-Discovery`.
- Evidencia:
  - `docs/memory/T8_0_1_FINANCAS_PESSOAIS_DISCOVERY.md`
  - `docs/adr/0003-segregacao-financas-pessoais.md`

### T8.1.1 (CONCLUIDA)
- Objetivo: MVP tecnico de segregacao por usuario/colaborador.
- Status: concluida em 26/02/2026.
- Escopo: backend + auth + privacidade.
- Conflito Codex x Antigravity: medio.
- Branch sugerida: `main-etapa-8.1-FinancasPessoais-MVP`.
- DoD:
  - `cd workspaces/backend && source .venv/bin/activate && python manage.py check && make lint && make test`
  - `bash scripts/quality_gate_all.sh`
  - `bash scripts/sync_memory.sh --check`

### T8.1.2 (CONCLUIDA)
- Objetivo: politicas operacionais de LGPD para dados pessoais (retencao, exportacao e trilha de acesso).
- Status: concluida em 26/02/2026.
- Escopo: backend + docs + runbooks.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-8.1-FinancasPessoais-LGPD-Operacional`.

### T8.2.1 (CONCLUIDA)
- Objetivo: discovery da proxima fase de financas pessoais (integracoes, UX e escopo de produto).
- Status: concluida em 26/02/2026.
- Escopo: docs + arquitetura + backlog.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-8.2-FinancasPessoais-Discovery2`.
- Evidencia:
  - `docs/memory/T8_2_1_FINANCAS_PESSOAIS_EVOLUCAO_DISCOVERY.md`
  - `docs/adr/0005-evolucao-financas-pessoais-fase-8-2.md`

### T8.2.2 (CONCLUIDA)
- Objetivo: implementacao da evolucao MVP (recorrencia, resumo mensal e importacao CSV com preview).
- Status: concluida em 26/02/2026.
- Escopo: backend + API + testes + docs.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-8.2-FinancasPessoais-MVP2`.

### T8.2.3 (P2 - proxima execucao)
- Objetivo: hardening pos-MVP da trilha pessoal (observabilidade, operacao de jobs e refinamento de contratos).
- Escopo: backend + operacao + docs.
- Conflito Codex x Antigravity: baixo.
- Branch sugerida: `main-etapa-8.2-FinancasPessoais-Hardening`.
