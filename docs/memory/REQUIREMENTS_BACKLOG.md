# Requirements Backlog (fonte unica do chat)

Referencia: 25/02/2026.
Escopo: consolidacao de requisitos funcionais/operacionais solicitados no chat.

## 1) Matriz de alinhamento (solicitacoes do chat x docs)

| Solicitacao do chat | Documento que cobre | Status | Acao necessaria |
|---|---|---|---|
| Operar sempre via VM (SSH) e manter contexto remoto | `docs/memory/RUNBOOK_DEV.md`, `docs/memory/PATHS_AND_PORTS.md` | parcial | doc: explicitar fluxo de retomada e padrao tmux persistente |
| Usar tmux com `codex`, `backend_live`, `portal_live`, `client_live` | `docs/memory/CHANGELOG.md`, `docs/memory/PROJECT_STATE.md` | parcial | doc: consolidar procedimento operacional no runbook |
| Diagnostico seguro antes de codar | `docs/memory/RECOVERY_TEMPLATE.md`, `.agent/workflows/W25_recovery_readonly.md` | OK | manter |
| Nao alterar codigo no inicio / modo read-only | `.agent/workflows/W25_recovery_readonly.md` | OK | manter |
| Validar branch policy real (`main`, `AntigravityIDE`, `Antigravity_Codex`) | `docs/memory/BRANCH_POLICY.md`, `docs/memory/PROJECT_STATE.md`, `.agent/workflows/USAGE_GUIDE.md` | OK | manter |
| GEMINI global-only (`~/.gemini/GEMINI.md`) | `GEMINI.md`, `docs/memory/GEMINI_SNAPSHOT.md`, `docs/memory/RUNBOOK_DEV.md` | OK | manter |
| Validar `gemini_check`, `branch_guard`, `sync_memory --check` | `docs/memory/RUNBOOK_DEV.md`, `.agent/workflows/W21_sync_codex_antigravity.md` | OK | manter |
| Remover lock Next apenas se orfao | `scripts/start_client_dev.sh`, `docs/memory/RUNBOOK_DEV.md` | parcial | doc: incluir passo claro de validacao de processo antes do `rm lock` |
| Subir servicos por scripts oficiais | `docs/memory/PROJECT_STATE.md`, `docs/memory/RUNBOOK_DEV.md` | OK | manter |
| Rodar smoke stack/client e quality gate | `docs/memory/RUNBOOK_DEV.md`, `.agent/workflows/W16_auditoria_qualidade.md` | OK | doc: reforcar execucao sem conflito com tmux live |
| Evitar conflito com Antigravity no portal template (6.2) | `docs/memory/PARALLEL_DEV_RULES.md`, `docs/memory/BRANCH_POLICY.md` | parcial | doc: registrar regra explicita de ownership temporario do portal |
| Consolidar plano completo implementado x pendente | `docs/memory/ROADMAP_MASTER.md`, `docs/memory/BACKLOG.md`, `docs/memory/PROJECT_STATE.md` | OK | manter |
| Fechar 7.1 Auth/RBAC end-to-end | `docs/memory/CHANGELOG.md`, `docs/memory/PROJECT_STATE.md`, `.agent/memory/TODO_NEXT.md` | OK | manter |
| Planejar 7.2 pagamentos online (PIX/cartao/VR + webhooks/idempotencia) | `docs/10-plano-mvp-cronograma.md`, `docs/memory/DECISIONS.md`, `docs/memory/CHANGELOG.md` | OK | manter |
| Planejar 6.3 Portal CMS backend-only | `docs/memory/ROADMAP_MASTER.md`, `docs/memory/BACKLOG.md`, `docs/memory/CHANGELOG.md` | OK | manter |
| Incluir Frontend de Gestao completo (novo epico obrigatorio) | `docs/memory/ROADMAP_MASTER.md`, `docs/memory/BACKLOG.md`, `docs/memory/PROJECT_STATE.md` | parcial | implementacao: continuar trilha T9.x ate cobertura total dos modulos |
| Seeds dinamicos (fotos/OCR/nutricao/produto montado) idempotentes | `docs/memory/CHANGELOG.md`, `docs/memory/DECISIONS.md` | parcial | implementacao: ampliar dataset e validacoes de qualidade de seed |

## 2) Requisitos consolidados por area (status)

### A) Backend e integracoes
- Catalog (ingredientes, pratos, cardapio por dia): **feito**
- Inventory (saldo/movimentos): **feito**
- Procurement (requisicoes, compras, AP): **feito**
- Orders (pedidos, payments, AR + cash + ledger): **feito**
- Finance (cashflow, DRE, KPIs, conciliacao, fechamento): **feito**
- Production (lotes, consumo estoque): **feito**
- Media upload + OCR jobs + nutricao: **feito (MVP)**
- Auth/RBAC 7.1 + endpoints publicos read-only de menu: **feito**

### B) Portal institucional (www)
- Template/layout clean com cardapio real-time e QR: **em progresso**
- SEO e paginas completas (`/sobre`, `/como-funciona`, `/contato`, `/app`): **em progresso**
- Observacao de conflito: implementacao visual 6.2 em paralelo no contexto Antigravity.

### C) Client web (cliente final)
- Login/conta/pedidos/historico: **feito**
- Checkout com pagamento online (PIX/cartao/VR): **feito (T7.2.3)**
- Remocao do modo demo: **feito**

### D) Frontend de Gestao (novo epico obrigatorio)
- Dashboard operacional: **feito (MVP T9.0.2)**
- Cardapio (CRUD): **pendente**
- Compras + anexos + OCR: **pendente**
- Estoque: **feito (MVP T9.0.2)**
- Producao: **pendente**
- Pedidos: **feito (MVP T9.0.2)**
- Financeiro: **feito (MVP T9.0.2)**
- Portal CMS: **pendente (integracao no Admin Web)**
- Usuarios/RBAC: **pendente**
- Relatorios/exportacoes: **pendente**

### E) Portal CMS via DB/API
- Config + Sections por template/pagina: **feito (T6.3.1)**
- API publica read-only para portal: **feito (T6.3.1)**
- Endpoints de administracao (backend/admin web): **feito no backend (T6.3.1), pendente no Admin Web**

### F) Pagamentos online (7.2)
- PIX + cartao + VR/VA (MVP): **feito (mock provider)**
- Webhooks + idempotencia: **feito (backend)**
- Integracao com finance/ledger/conciliation/close: **feito (backend)**

### G) Financas pessoais (8)
- Segregacao por usuario/colaborador: **pendente**
- Privacidade/LGPD especifica: **pendente**

### H) Infra nao critica
- Nginx/proxy dev e deploy/dns: **pendente**

### I) Seeds e dados dinamicos
- Seed idempotente de cadeia completa: **feito**
- Dados reais ampliados (fotos/OCR/nutricao/produto montado): **em progresso**

## 3) Observacoes operacionais
- Politica de branches valida: Codex (`main`, `main-etapa-*`), Antigravity (`AntigravityIDE`, `AntigravityIDE/etapa-*`), Union (`Antigravity_Codex`).
- Enquanto a trilha visual 6.2 estiver ativa no Antigravity, evitar mudancas concorrentes de layout do portal pelo Codex.
- Prioridade funcional atual para receita/operacao: **9.0 Admin Web (T9.0.3) + 6.3.2 Integracao CMS no portal**.
