# Plano T9.2.1 - Testes manuais E2E da aplicacao

Data: 2026-02-26

## Objetivo
Definir e institucionalizar uma campanha manual E2E para validar todos os fluxos criticos do ecossistema Mr Quentinha (backend, portal, client, admin e release mobile), com registro de evidencias e plano de correcao.

## Escopo coberto
- Autenticacao (JWT e preparo de social login Google/Apple)
- Catalogo, pedidos, pagamentos e historico no web client
- Configuracao multigateway (Mercado Pago, Efi, Asaas) no Portal CMS e sincronizacao de status em tempo real
- Modulos operacionais no Admin Web (cardapio, compras, estoque, producao, financeiro, portal CMS, usuarios/RBAC, relatorios)
- Portal institucional e distribuicao de app/release mobile
- APIs publicas e privadas do backend (incluindo ownership/RBAC)
- Trilha de financas pessoais (MVP + evolucao 8.2.2)

## Pre-requisitos de execucao
1. Ambiente local ativo com scripts oficiais:
   - `bash scripts/start_backend_dev.sh`
   - `bash scripts/start_portal_dev.sh`
   - `bash scripts/start_client_dev.sh`
   - `bash scripts/start_admin_dev.sh`
2. Massa de dados base aplicada:
   - `bash scripts/seed_demo.sh`
3. Sanidade automatizada antes da rodada manual:
   - `bash scripts/smoke_stack_dev.sh`
   - `bash scripts/smoke_client_dev.sh`
4. Build/lint/test em estado verde:
   - `bash scripts/quality_gate_all.sh`

## Checklist E2E manual (macro)
### Bloco A - Acesso e autenticacao
- [ ] A1: login/logout via JWT no client web e admin web.
- [ ] A2: cadastro de novo cliente e acesso ao cardapio.
- [ ] A3: fluxo de OAuth Google no client (botao, redirecionamento, callback com `code`).
- [ ] A4: fluxo de OAuth Apple no client (botao, redirecionamento, callback com `code`).
- [ ] A5: validar que segredo OAuth nao aparece no payload publico `/api/v1/portal/config/`.

### Bloco B - Jornada cliente
- [ ] B1: leitura de cardapio por data e troca de template do canal client pelo CMS.
- [ ] B2: carrinho -> checkout -> pedido criado -> status visivel em `Meus pedidos`.
- [ ] B3: pagamento online com intent (PIX/CARD/VR) e atualizacao de status no historico.
- [ ] B3.1: validar habilitacao dinamica de metodos no checkout conforme `payment_providers` publicado.
- [ ] B3.2: validar fluxo PIX por provider (Mercado Pago, Asaas, Efi) com confirmacao realtime.
- [ ] B3.3: validar fluxo cartao por provider habilitado e retorno de status para `Meus pedidos`.
- [ ] B3.4: validar provider por canal (`web` x `mobile`) no CMS e confirmar roteamento de intent por `X-Client-Channel`.
- [ ] B4: confirmacao de recebimento e reflexo no backend.

### Bloco C - Operacao interna (Admin)
- [ ] C1: cardapio completo (ingrediente, prato, composicao, menu do dia).
- [ ] C2: compras (requisicao por cardapio, compra, anexos/OCR, impacto em estoque/AP).
- [ ] C3: estoque (movimentos e consistencia de saldo).
- [ ] C4: producao (lote, consumo de insumo, fechamento).
- [ ] C5: financeiro (AP/AR/caixa/ledger/conciliacao/relatorios).
- [ ] C6: usuarios e RBAC (atribuicao de roles e bloqueio de acesso indevido).
- [ ] C7: portal CMS (template, secoes, conectividade, autenticacao social, release mobile).
- [ ] C8: portal CMS pagamentos (roteamento por metodo, recebedor CPF/CNPJ, teste de conexao por provider).
- [ ] C9: modulo `Monitoramento` e dashboard com dados realtime de servicos, gateways e lifecycle do pedido.

### Bloco D - Portal e distribuicao do app
- [ ] D1: portal institucional renderizando template ativo em runtime.
- [ ] D2: pagina `/app` consumindo release publicada e redirecionamentos de download.
- [ ] D3: consistencia visual da marca (logo/tokens/cor primaria) em light/dark.

### Bloco E - Financas pessoais
- [ ] E1: CRUD de contas/categorias/lancamentos/orcamentos por ownership.
- [ ] E2: recorrencia idempotente e resumo mensal.
- [ ] E3: importacao CSV preview/confirm sem duplicidade.
- [ ] E4: exportacao e auditoria LGPD.

## Evidencias obrigatorias por rodada
- Data/hora da execucao
- Ambiente/branch
- Fluxos executados (IDs do checklist)
- Resultado por fluxo (`PASS`/`FAIL`)
- Links/prints/logs do erro
- Plano de correcao com owner e prazo

## Cadencia proposta
- Rodada curta diaria (20-30 min): blocos A+B essenciais + smoke visual.
- Rodada completa semanal (90-150 min): blocos A..E com evidencia formal.
- Rodada de pre-release: obrigatoria antes de publicacao de template ou release mobile.

## Metas no roadmap global (T9.2.1)
- `T9.2.1-A1` (concluida em 26/02/2026): publicar plano unificado e atualizar docs de memoria.
- `T9.2.1-A2` (pendente): executar primeira rodada manual completa A..E com relatorio de evidencias.
- `T9.2.1-A2` (pendente): executar primeira rodada manual completa A..E incluindo matrix multigateway.
- `T9.2.1-A3` (pendente): transformar falhas da rodada em backlog priorizado com owners.
- `T9.2.1-A4` (pendente): institucionalizar rotina semanal fixa no runbook operacional.

## Registro da rodada atual
- Status da rodada manual completa: **em execucao** (rodada `T9.2.1-A2` iniciada em 27/02/2026).
- Status da preparacao automatizada: usar `quality_gate_all` + smokes como porta de entrada da rodada manual.
- Relatorio oficial da rodada atual: `docs/memory/T9_2_1_A2_RELATORIO_EXECUCAO_2026-02-27.md`.
