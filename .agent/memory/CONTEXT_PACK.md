# Context Pack (Resumo Operacional)

## Mapa rapido do repo
- `AGENTS.md` (regras centrais)
- `/home/roberto/.gemini/GEMINI.md` (fonte unica de policy)
- `docs/memory/*` (estado, decisoes, changelog, runbook, roadmap, backlog)
- `scripts/*` (start/smoke/seed/sync/quality/branch_guard/union)
- `workspaces/backend` (API Django/DRF)
- `workspaces/web/portal` (portal institucional)
- `workspaces/web/client` (web cliente)
- `workspaces/web/admin` (admin web de gestao)
- `workspaces/web/ui` (UI compartilhada)
- `.agent/workflows/*` (mapa operacional)

## Estado atual
- Atualizacao em 02/03/2026 (seguranca/midia): documentos, selfie e biometria do perfil agora usam URL assinada temporaria via endpoint `accounts/profile-media`; acesso direto a `/media/accounts/profile|documents|biometric/*` foi bloqueado.
- Atualizacao em 02/03/2026 (seguranca/hardening): execucao inicial do plano aprovado concluida com `manage.py` deterministico (env/.env), hardening de `config.settings.prod`, derivacao forte de `SECRET_KEY` no `installdev.sh` e `setup_nginx_prod.sh` com redirect HTTP->HTTPS + headers de seguranca.
- Atualizacao em 02/03/2026 (auditoria): rodada completa de auditoria estatica (seguranca/qualidade/redundancias) concluida e publicada em `docs/reports/`, com plano priorizado `P0/P1/P2` aprovado para execucao.
- Atualizacao em 02/03/2026 (web admin/navegacao): menu `Prioridades` foi substituido por `Sobre`; rota legada `/prioridades` agora redireciona para `/sobre`.
- Atualizacao em 02/03/2026 (CEP/global): `FormFieldGuard` passou a exibir feedback de status de CEP (digitacao parcial, consultando, encontrado, nao encontrado, erro) e manter autopreenchimento de endereco no mesmo padrao para Admin, Web Client e Portal em todos os templates.
- Atualizacao em 02/03/2026 (perfil/CEP): `/perfil` agora mostra status de busca de CEP e preenche endereco automaticamente; backend passou a priorizar fallback ViaCEP quando Correios estiver indisponivel.
- Atualizacao em 02/03/2026 (ops/producao): novo iniciador `scripts/start_ops_dashboard_prod.sh` para abrir o painel de operacao de producao com um comando unico.
- Atualizacao em 02/03/2026 (web admin/auth): shell do Admin agora oculta menu e navegacao antes do login; filtragem de menus por permissao de modulo do usuario aplicada em todos os templates.
- Atualizacao em 02/03/2026 (web admin/perfil): `Meu Perfil` passou a carregar/salvar tambem dados da conta (`username`, `email`, `first_name`, `last_name`) via novo `PATCH /api/v1/accounts/me/`.
- Atualizacao em 02/03/2026 (ops/media): script `scripts/fix_media_permissions.sh` padroniza ownership/permissoes do `MEDIA_ROOT`; backend exposto para servir `/media/*` em runtime com proxy atual.
- Atualizacao em 02/03/2026 (web admin): preload global de rede reativado no layout e validacao de senha forte adicionada no modulo `Usuarios e RBAC`; regra global agora exige validar qualquer correcao nos tres templates do Admin (`classic`, `adminkit`, `admindek`).
- Atualizacao em 02/03/2026 (instalacao hibrida EC2): `installdev.sh` reexecutado com Postgres local, bancos separados (`mrquentinha_dev`/`mrquentinha_prod`), Nginx ativo e smoke de stack validado em `172.31.71.156`.
- Atualizacao em 02/03/2026 (hardening instalador): `installdev.sh` passou a respeitar `MRQ_DB_HOST` no provisionamento e remover `*.trycloudflare.com` do `.env.prod` (restrito ao DEV).
- Atualizacao em 02/03/2026 (seguranca operacional): segredos da maquina padronizados fora do Git em `/home/ubuntu/.mrquentinha-secure/host-secrets.env`, com carga no workflow de inicio (`W10_iniciar_sessao`).
- Atualizacao em 01/03/2026 (`T9.2.6-A3`): padrao global de formularios evoluido com lookup automatico de CEP (Correios), autopreenchimento de endereco, mascara/validacao de telefone em tempo real e validacao servidor-side de CPF/CNPJ por DV.
- Atualizacao em 01/03/2026 (`T9.2.6-A3`): backend ganhou endpoint publico `GET /api/v1/accounts/lookup-cep/?cep=...` e perfil de usuario passou a persistir `phone_is_whatsapp`.
- Atualizacao em 01/03/2026 (`T9.2.7-A4-HF2`): auditoria de atividade foi separada de `Administracao do servidor` e ganhou modulo proprio `/modulos/auditoria-atividade` com dashboard/KPIs, filtros e analise de seguranca/tendencias.
- Atualizacao em 01/03/2026 (`T9.2.7-A4-HF2`): backend `admin_audit` evoluiu com endpoint `GET /api/v1/admin-audit/admin-activity/overview/` para agregacoes operacionais da trilha administrativa.
- Atualizacao em 01/03/2026 (`T9.2.7-RBAC-HF1`): modulo `Usuarios e RBAC` evoluiu para gestao completa de usuarios internos no Web Admin (criar/editar conta, atribuir papeis e tarefas por categoria), com novos endpoints em `accounts` e cobertura de testes no backend.
- Atualizacao em 01/03/2026 (`T9.2.7-RBAC-HF1`): modulos tecnicos do Admin (`Portal CMS`, `Administracao do servidor`, `Instalacao / Deploy`, `Usuarios e RBAC`) passaram a ter bloqueio explicito para perfis sem `ADMIN`.
- Atualizacao em 01/03/2026 (`T9.2.7-A5-A2/planejamento`): plano formal AWS-first publicado em `docs/11-plano-cloud-aws-google-e-testes-operacionais.md`, incluindo backlog de paridade Google Cloud e campanha de testes operacionais guiados.
- Atualizacao em 01/03/2026 (`T9.2.7-A5-A1`): assistente de instalacao evoluiu com execucao remota real via SSH (probe de conectividade + job em background + logs/exit code) e validacao de conectividade cloud para `aws/gcp` antes de aceitar plano de deploy.
- Atualizacao em 01/03/2026 (`T9.2.7-A5-A2`): assistente de instalacao evoluiu com trilha AWS dedicada (credenciais seguras em runtime, endpoint de validacao AWS, checks de Route53/EC2/EIP/CodeDeploy e painel de custos estimados + MTD no passo `Infraestrutura`).
- Atualizacao em 01/03/2026 (`T9.2.7-A5-A2-HF1`): `Portal CMS` ganhou links diretos para cadastro/setup/documentacao de Google/Apple e Mercado Pago/Efi/Asaas, no proprio contexto de preenchimento dos formularios.
- Atualizacao em 01/03/2026 (`T9.2.7-A5-A2-HF1`): guia manual de instalacao por cenarios publicado em `docs/12-guia-testes-instalacao-manual.md`.
- Atualizacao em 01/03/2026 (`T9.2.7-A6`): dados sensiveis do `UserProfile` criptografados com hashes de busca, novos endpoints de suporte ao cliente (admin/cliente) e listagem administrativa de inscritos para notificacoes.
- Atualizacao em 01/03/2026 (`T9.2.7-A6`): web admin ganhou guias individuais por modulo Business, aba de suporte/notificacoes em Clientes e preload global removido; web client/portal receberam paginas de Privacidade/Termos/LGPD com links no footer.
- Atualizacao em 02/03/2026 (`T9.2.7-A6`): Ops Dashboard ganhou box de Postgres local; script `installdev.sh` e guia AWS preconfig com db dev/prod publicados.
- Atualizacao em 02/03/2026 (ops/rules): regra global passou a exigir teste ao final de qualquer acao; `ops_dashboard` corrigido para evitar `UnboundLocalError` em `draw_box`.
- Atualizacao em 02/03/2026 (ops/cloud): SSL/TLS via Web Admin (certbot) + scripts `setup_nginx_prod.sh`/`ops_ssl_cert.sh`; modo DEV oficial com dominio + portas no Cloudflare.
- Atualizacao em 28/02/2026 (`T9.2.7-A4`): backend ganhou app `admin_audit` com trilha de atividade administrativa e endpoint `GET /api/v1/admin-audit/admin-activity/`; Web Admin ganhou secao `Auditoria de atividade` em `Administracao do servidor`.
- Atualizacao em 28/02/2026 (`T9.2.7-A4`): conectividade Cloudflare DEV evoluiu com `dev_url_mode` (`random`/`manual`) e `dev_manual_urls` editaveis para `portal/client/admin/api`, permitindo enderecamento DEV estavel para homologacoes longas/mobile.
- Atualizacao em 28/02/2026 (`T9.2.7-A3`): `Administracao do servidor` ganhou painel `Assistente de instalacao` com wizard guiado, validacao por etapa, autosave e monitoramento de jobs via backend (`installer_settings` + endpoints `installer-*`).
- Atualizacao em 28/02/2026 (`T9.2.7-A3`): workflow continuo do instalador padronizado com `scripts/check_installer_workflow.sh`, integrado no `session`, `sync_memory` e `quality_gate_all`.
- Atualizacao em 27/02/2026 (`T9.2.1-A2-HF6`): Web Admin ganhou gestao de e-mail (SMTP + teste de envio) no modulo Portal CMS; regra de login foi refinada para exigir validacao de e-mail somente para contas cliente, sem bloquear perfis administrativos/gestao.
- Atualizacao em 27/02/2026 (`T9.2.1-A2-HF4`): fluxo de confirmacao de e-mail implantado no cadastro do web client com link dinamico por ambiente (origem ativa DEV + fallback `PortalConfig.client_base_url`), endpoint de confirmacao/reenvio no backend e visibilidade de compliance no Admin (`usuarios-rbac`).
- Atualizacao em 27/02/2026 (`T9.2.1-A2-HF5`): login de conta cliente sem e-mail validado bloqueado no endpoint JWT; reenvio de token liberado por `identifier` no login; token de confirmacao reduzido para 3h com template HTML de e-mail (logo + dados dinâmicos do CMS).
- Concluido: `0 -> 5.6.3`, `6.0`, `6.0.1`, `7.0`, `7.1.1`, `7.1.2`, `7.1.3`, `7.2.1`, `7.2.2`, `7.2.3`, `6.3.1`, `6.1.1`, `9.0.1`, `9.0.2`, `9.0.3`, `9.1.1`, `9.1.2`, `9.1.3-A7`, `6.3.2-A3`, `6.3.2-A4`, `6.3.2-A5`, `T9.1.1-HF1`, `T9.1.1-HF2`, `T9.1.1-HF3`, `T9.1.1-HF4`.
- Etapa ativa: `6.2` (ownership Antigravity para consolidacao visual do portal).
- Proxima subetapa recomendada para Codex: `T9.2.1-A2` (rodada manual E2E completa) com evolucao tecnica paralela em `T9.2.7-A4` (automacao remota SSH/AWS/GCP do assistente).
- Entrega parcial de `T6.3.2` concluida em 26/02/2026: Admin Web ganhou modulo `Portal CMS` com selecao de template ativo e acao de publicacao da configuracao.
- Entrega parcial de `T6.3.2` concluida em 26/02/2026: Portal Web passou a ler `active_template` direto do CMS (`/api/v1/portal/config/`) em runtime.
- Entrega parcial de `T6.3.2` concluida em 26/02/2026: Portal e Client ganharam fallback automatico de API para host local (`:8000`) quando env nao estiver definida.
- Entrega parcial de `T9.1.3` concluida em 26/02/2026: Admin Web cobriu ciclo operacional de composicao de prato, compras e periodos diarios de refeicao.
- Entrega complementar de `T9.1.3` concluida em 26/02/2026: Cardapio no Admin com edicao de prato/insumo e composicao completa.
- Entrega complementar de `T9.1.3` concluida em 26/02/2026 (`A5`): fotos de pratos/insumos sincronizadas no banco com fallback local e retorno da composicao com `image_url` no cardapio para portal/client/mobile.
- Entrega complementar de `T9.1.3` concluida em 26/02/2026 (`A6`): fluxo de compras no Admin com captura/upload por camera para comprovante e produto, OCR aplicado automaticamente e persistencia das fotos no destino final (`purchase`/`purchase_item`).
- Entrega complementar de `T9.1.3` concluida em 26/02/2026 (`A7`): painel operacional em linha de producao (dashboard realtime), auto-geracao de requisicao de compras a partir do cardapio e ciclo de entrega com confirmacao de recebimento no frontend cliente.
- Entrega concluida em 26/02/2026 (`T6.3.2-A3`): midias LetsFit dinamicas no CMS/Portal, editor de secoes no Admin e upload de fotos para insumos/pratos com contrato compartilhado para mobile.
- Entrega concluida em 26/02/2026 (`T6.3.2-A4`): Web Cliente integrado ao CMS para escolher template por canal (`client-classic`/`client-quentinhas`), com leitura server-side em runtime e ajuste visual no layout principal.
- Entrega concluida em 26/02/2026 (`T6.3.2-A5`): Portal CMS ganhou secao de conectividade para configurar dominio/subdominios e URLs de Portal/Client/Admin/API/Proxy no modo dev local (host `mrquentinha`), incluindo lista de origens CORS.
- Entrega concluida em 26/02/2026 (`T7.2.3-HF2`): fluxo do cliente web revisado ponta a ponta (login -> pedido -> recebimento), com guia UX de jornada, diagnostico de API em tela, guard de autenticacao no checkout e compatibilidade validada para execucao do client em `localhost:3000`.
- Hotfix mais recente: rotas diretas do Admin (`/modulos` e `/prioridades`) corrigidas com redirect para as ancoras da home, eliminando 404 em acesso por URL direta.
- Fechamento T9.1.2: relatorios ativos no Admin com exportacao CSV por modulo (Pedidos/Compras/Producao/Financeiro/Relatorios), filtro por periodo e rotulos pt-BR de status operacionais.
- Ajuste UX: menus dos modulos filtram blocos por servico (modo completo ou foco) e dashboard do Admin indica etapa 9.1 concluida.

## Fonte de planejamento
- `docs/memory/REQUIREMENTS_BACKLOG.md`
- `docs/memory/ROADMAP_MASTER.md`
- `docs/memory/BACKLOG.md`
- `.agent/memory/TODO_NEXT.md`

## Portas e scripts
- Backend `8000` -> `scripts/start_backend_dev.sh`
- Portal `3000` -> `scripts/start_portal_dev.sh`
- Client `3001` -> `scripts/start_client_dev.sh`
- Admin `3002` -> `scripts/start_admin_dev.sh`
- Proxy local `8088` -> `scripts/start_proxy_dev.sh`
- Smokes -> `scripts/smoke_stack_dev.sh`, `scripts/smoke_client_dev.sh`, `scripts/smoke_proxy_dev.sh`
- Quality -> `scripts/quality_gate_all.sh`
- Sync -> `scripts/sync_memory.sh --check`

## Regra critica
- Sem segredos no repositorio.
- Evitar conflito de portal enquanto `6.2` estiver ativo no Antigravity.
- Branch Codex por tarefa (`main-etapa-*`) e merge rapido de volta em `main` apos quality gate.
