# TODO Next (fila cronologica)

Historico recente:
1. [x] 7.1.1 Backend Auth/RBAC (ownership orders/payments) - concluida em 24/02/2026.
2. [x] 7.1.2 Client Auth real (login/register/me + refresh, sem demo) - concluida em 24/02/2026.
3. [x] 7.1.3 Fechamento 7.1 (quality gate + smokes + docs/memory) - concluida em 25/02/2026.
4. [x] T7.2.1 Pagamentos online: provider abstraction + payment intents + idempotencia (backend) - concluida em 25/02/2026.
5. [x] T7.2.2 Pagamentos online: webhook idempotente + reconciliacao financeira (AR/cash/ledger) - concluida em 25/02/2026.
6. [x] T7.2.3 Client checkout online (PIX/cartao/VR) consumindo intents/status - concluida em 25/02/2026.
7. [x] T6.3.1 Portal CMS backend-only (Config/Sections + API publica/admin) - concluida em 25/02/2026.
8. [x] T9.0.1 Admin Web MVP foundation (auth shell + dashboard inicial) - concluida em 25/02/2026.
9. [x] T9.0.2 Admin Web MVP operacional (Pedidos, Financeiro, Estoque) - concluida em 25/02/2026.
10. [x] T9.0.3 Admin Web expansion (baseline Cardapio/Compras/Producao) - concluida em 25/02/2026.
11. [x] T9.1.1 Admin Web completo: fluxo operacional de Cardapio/Compras/Producao + Usuarios/RBAC - concluida em 25/02/2026.
12. [x] T6.1.1 Nginx/proxy local em janela dedicada - concluida em 25/02/2026.
13. [x] T9.1.1-HF1 Hotfix Admin Web login: corrigir crash client-side ao digitar usuario e liberar `allowedDevOrigins` para acesso via IP - concluida em 25/02/2026.
14. [x] T9.1.1-HF2 Hotfix Admin Web login: liberar CORS backend para `:3002`, fallback de API base no Admin e feedback inline de erro no login - concluida em 25/02/2026.
15. [x] T9.1.1-HF3 UX/Branding: cores de status padronizadas e logo oficial aplicada em Admin/Portal/Client - concluida em 25/02/2026.
16. [x] T9.1.1-HF4 Hotfix Admin rotas: acesso direto `/modulos` e `/prioridades` com redirect para ancora - concluida em 25/02/2026.

Fila atual:
17. [ ] T6.2.1 Consolidacao visual portal `letsfit-clean` (ownership Antigravity, sem conflito).
18. [x] T6.3.2 Integracao CMS no portal (Codex) - concluida em 26/02/2026.
19. [x] T9.1.2 Admin Web relatorios/exportacoes (hotpages, menus contextuais, graficos e exportacao CSV por modulo) - concluida em 25/02/2026.
20. [x] T6.3.2-A1 Admin Web `Portal CMS`: selecao de template ativo + publicacao da configuracao - concluida em 26/02/2026.
21. [x] T6.3.2-A2 Portal Web: leitura server-side de `active_template` do CMS com fallback `classic` - concluida em 26/02/2026.
22. [x] T6.3.2-A2-HF1 Portal/Web Client: fallback de API por host local e hardening de rede/CORS no frontend - concluida em 26/02/2026.
23. [x] T9.1.3-A1/A2/A3 Admin Web ciclo operacional: composicao de prato + registro de compra + periodos de refeicao - concluida em 26/02/2026.
24. [x] T6.3.2-A3 Midias LetsFit multi-frontend (backend, portal, client, mobile) com catalogo unico de fotos - concluida em 26/02/2026.
25. [x] T9.1.3-A4 Cardapio concluido no Admin: edicao de pratos/insumos e composicao completa com validacoes de operacao - concluida em 26/02/2026.
26. [x] T9.1.3-A5 Fotos dinamicas de pratos + insumos no banco/API para todos os frontends - concluida em 26/02/2026.
27. [x] T9.1.3-A6 Captura/upload de imagens de compra + OCR com persistencia no destino final - concluida em 26/02/2026.
28. [x] T9.1.3-A7 Ciclo operacional completo (linha de producao + dashboard realtime + entrega/confirmacao) - concluida em 26/02/2026.
29. [x] T7.2.3-HF2 Fluxo cliente web ponta a ponta + hardening localhost:3000 - concluida em 26/02/2026.
30. [x] T6.3.2-A4 Web Cliente com template dinamico via CMS (client-classic/client-quentinhas) + seletor no Admin Web - concluida em 26/02/2026.
31. [x] T6.3.2-A5 Portal CMS: configuracao de dominios/subdominios e conectividade local (host `mrquentinha`) para Portal/Client/Admin/API - concluida em 26/02/2026.
32. [x] T8.0.1 Financas pessoais (discovery LGPD + segregacao) - concluida em 26/02/2026.
33. [x] T9.2.1-A2-HF4 Confirmacao de e-mail no cadastro do web client com URL dinamica DEV/PROD + compliance no Admin - concluida em 27/02/2026.
34. [x] T9.2.1-A2-HF5 Bloqueio de login sem validacao de e-mail + reenvio publico de token + TTL 3h + template HTML dinamico - concluida em 27/02/2026.
35. [x] T9.2.1-A2-HF6 Gestao de e-mail no Web Admin (SMTP + teste) e correção da regra de login para bloquear validacao de e-mail apenas no fluxo cliente - concluida em 27/02/2026.
36. [x] T9.2.7-A3 Assistente de instalacao/deploy no modulo Administracao do servidor + workflow continuo de atualizacao do instalador - concluida em 28/02/2026.
37. [x] T9.2.8-A1 Assistente migrado para modulo independente `Instalacao / Deploy` + pre-requisitos obrigatorios de producao (DNS/servidor e gateway) com modal de correcao no wizard - concluida em 28/02/2026.
38. [x] T9.2.7-A4 Auditoria administrativa do Web Admin + Cloudflare DEV com `dev_url_mode` (`random`/`manual`) e URLs manuais editaveis - concluida em 28/02/2026.
39. [ ] T9.2.7-A5 Evoluir execucao remota do assistente (SSH/AWS/GCP) com automacao completa de provisionamento e validacoes de conectividade.  
   - Progresso 01/03/2026 (`A1`): execucao remota real via SSH implementada (probe + job em background + logs), validacao de conectividade para AWS/GCP adicionada.
   - Progresso 01/03/2026 (`A2/planejamento`): plano detalhado da trilha AWS + backlog de paridade Google Cloud + testes operacionais guiados publicado em `docs/11-plano-cloud-aws-google-e-testes-operacionais.md`.
   - Progresso 01/03/2026 (`A2/implementacao inicial`): wizard ganhou trilha AWS com validacao segura (`profile`/`access_key`), endpoint `installer-cloud/aws/validate`, checks de infraestrutura (Route53/EC2/EIP/CodeDeploy) e painel de custos (estimativa + MTD via Cost Explorer quando disponivel).
   - Progresso 01/03/2026 (`A2/HF1`): `Portal CMS` passou a exibir links de onboarding para OAuth social e gateways; guia de teste manual do instalador por cenarios publicado em `docs/12-guia-testes-instalacao-manual.md`.
40. [x] T9.2.7-RBAC-HF1 Gestao completa de usuarios no Web Admin (criar/editar conta, papeis, categorias/tarefas e bloqueio de areas tecnicas para nao-admin) - concluida em 01/03/2026.
41. [x] T9.2.7-A4-HF2 Criar modulo dedicado `Auditoria de atividade` (separado de `Administracao do servidor`) com dashboard/KPIs, filtros e analise de seguranca - concluida em 01/03/2026.
42. [x] T9.2.6-A3 Padronizacao global de formularios: CEP Correios com autopreenchimento, mascara/validacao de telefone + checkbox WhatsApp e validacao de CPF/CNPJ por DV no backend - concluida em 01/03/2026.
43. [x] T9.2.7-A6 Suporte ao cliente + notificacoes, criptografia de dados sensiveis, guias de modulos Business e paginas LGPD/Privacidade/Termos no portal/client - concluida em 01/03/2026.
44. [x] T9.2.7-A6 Ops Dashboard com box Postgres + script installdev + guia AWS preconfig (db dev/prod) - concluida em 02/03/2026.
45. [x] Ops-02/03/2026 Instalacao hibrida real em EC2 t3.micro (Postgres local + DNS oficial + hardening `installdev.sh` + checkpoint de continuidade) - concluida em 02/03/2026.
46. [x] WebAdmin-02/03/2026 Corrigir preload global + endurecer acesso tecnico + validacao de senha no modulo Usuarios/RBAC (cobertura em todos os templates) - concluida em 02/03/2026.
47. [x] WebAdmin-02/03/2026 Hardening de acesso: ocultar menu pre-login, filtrar navegacao por permissao de modulo, corrigir `Meu Perfil` (dados de conta + dados adicionais) e revisar pipeline de media/upload em producao - concluida em 02/03/2026.
48. [x] Ops-02/03/2026 Dashboard de producao: launcher shell `start_ops_dashboard_prod.sh` adicionado para iniciar rapidamente o painel TUI de operacao - concluida em 02/03/2026.
49. [x] WebAdmin-02/03/2026 CEP no perfil: status visual de consulta + autopreenchimento de endereco e fallback ViaCEP no backend quando Correios indisponivel - concluida em 02/03/2026.
50. [x] Web-02/03/2026 CEP global: feedback padronizado (consultando/sucesso/nao encontrado/erro) e autofill validado para todos os formularios em Admin, Web Client e Portal (todos os templates) - concluida em 02/03/2026.
51. [x] WebAdmin-02/03/2026 Navegacao institucional: `Prioridades` substituido por `Sobre` com redirecionamento de compatibilidade - concluida em 02/03/2026.
52. [x] Ops-02/03/2026 Auditoria completa (seguranca + qualidade + evidencias + plano P0/P1/P2) publicada e aprovada para execucao - concluida em 02/03/2026.
53. [x] Ops-02/03/2026 Hardening inicial executado: settings deterministicas (`manage.py`), `SECRET_KEY` forte no instalador e HTTPS/headers reforcados em `prod.py` + `setup_nginx_prod.sh` - concluida em 02/03/2026.
54. [x] Ops-02/03/2026 Fase P0 midia sensivel: URL assinada para documentos/biometria no perfil e bloqueio de acesso direto em `/media/accounts/*` sensivel - concluida em 02/03/2026.
55. [x] Ops-02/03/2026 Automacao de continuidade DEV: script `sync_dev_from_main.sh` criado para sincronizacao segura e repetivel da VM DEV - concluida em 02/03/2026.
56. [x] Ops-02/03/2026 Hardening P1: token de webhook com comparacao em tempo constante + rate limit por IP e CORS/CSRF de producao restritos a HTTPS oficial no `installdev.sh` - concluida em 02/03/2026.
