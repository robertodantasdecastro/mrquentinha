# T9.2.1-A2 - Relatorio de Execucao Manual E2E

Data de abertura: 27/02/2026  
Responsavel da rodada: Operacao Mr Quentinha  
Escopo: backend + portal + web client + web admin + cloudflare dev + mobile release

## 1) Pre-check obrigatorio (entrada da rodada)
- [x] `bash scripts/smoke_stack_dev.sh` (OK na segunda execucao)
- [x] `bash scripts/smoke_client_dev.sh` (OK)
- [x] `GET /api/v1/health` (HTTP 200)
- [x] `GET /api/v1/health` via Cloudflare DEV (HTTP 200)
- [x] CORS via Cloudflare DEV validado para origens web (`access-control-allow-origin` retornando origem dinamica)

Observacao operacional:
- Durante a execucao automatizada desta sessao, o origin da porta `3001` apresentou intermitencia apos rotinas de smoke (impactando o dominio Cloudflare do Web Client).  
- Em validacao manual anterior reportada pelo operador, os 4 servicos (portal/client/admin/api) responderam online com check 200.
- Incidente tratado na rodada: crash/intermitencia no Web Client ao digitar em `/conta` no dominio Cloudflare DEV. Correcao aplicada em duas frentes:
  - hardening do `FormFieldGuard` global (captura de excecoes em `input/blur/submit`);
  - liberacao de `*.trycloudflare.com` em `allowedDevOrigins` de `client/admin/portal` para evitar bloqueio `/_next/*` no Next.js dev.
- Incidente tratado na rodada: runtime `TypeError` em `/conta` ao digitar (`Cannot read properties of null (reading 'value')`), causado por leitura de `event.currentTarget.value` dentro de updater assíncrono do React; corrigido com captura imediata do valor antes do `setState`.

## 2) Checklist E2E (status da rodada)

### Bloco A - Acesso e autenticacao
- [ ] A1: login/logout via JWT no client web e admin web.
- [ ] A2: cadastro de novo cliente e acesso ao cardapio.
- [ ] A3: fluxo de OAuth Google no client (botao, redirect, callback com `code`).
- [ ] A4: fluxo de OAuth Apple no client (botao, redirect, callback com `code`).
- [ ] A5: validar que segredos OAuth nao aparecem em `/api/v1/portal/config/`.

### Bloco B - Jornada cliente
- [ ] B1: leitura de cardapio por data e troca de template do canal client pelo CMS.
- [ ] B2: carrinho -> checkout -> pedido criado -> status em `Meus pedidos`.
- [ ] B3: pagamento online com intent (PIX/CARD/VR) e atualizacao de status.
- [ ] B3.1: habilitacao dinamica de metodos conforme `payment_providers`.
- [ ] B3.2: fluxo PIX por provider (Mercado Pago, Asaas, Efi).
- [ ] B3.3: fluxo cartao por provider habilitado.
- [ ] B3.4: provider por canal (`web` x `mobile`) com roteamento por `X-Client-Channel`.
- [ ] B4: confirmacao de recebimento e reflexo no backend.

### Bloco C - Operacao interna (Admin)
- [ ] C1: cardapio completo (ingrediente, prato, composicao, menu do dia).
- [ ] C2: compras (requisicao por cardapio, compra, OCR, impacto em estoque/AP).
- [ ] C3: estoque (movimentos e saldo).
- [ ] C4: producao (lote, consumo, fechamento).
- [ ] C5: financeiro (AP/AR/caixa/ledger/conciliacao/relatorios).
- [ ] C6: usuarios/RBAC (roles e bloqueio de acesso indevido).
- [ ] C7: portal CMS (template, secoes, conectividade, auth social, release mobile).
- [ ] C8: portal CMS pagamentos (metodos, recebedor, teste de conexao por provider).
- [ ] C9: monitoramento realtime no dashboard/modulo de monitoramento.

### Bloco D - Portal e distribuicao do app
- [ ] D1: portal renderizando template ativo em runtime.
- [ ] D2: pagina `/app` consumindo release publicada e redirecionamentos.
- [ ] D3: consistencia de identidade visual (logo/tokens/light-dark).

### Bloco E - Financas pessoais
- [ ] E1: CRUD com ownership por usuario.
- [ ] E2: recorrencia idempotente e resumo mensal.
- [ ] E3: importacao CSV preview/confirm sem duplicidade.
- [ ] E4: exportacao e auditoria LGPD.

## 3) Registro de evidencias da rodada

Formato por item:
- ID:
- Resultado: `PASS` | `FAIL`
- Evidencia (URL/print/log):
- Observacao:
- Acao corretiva (se FAIL):
- Owner:
- Prazo:
