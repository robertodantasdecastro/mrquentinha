# ADR 0009 - Gestao de e-mail no Web Admin e escopo da validacao de e-mail

- Status: Aceita
- Data: 27/02/2026

## Contexto
O ecossistema passou a exigir envio real de e-mails operacionais (confirmacao de conta, notificacoes) com credenciais administradas pelo painel.
Tambem foi identificado impacto indevido no login do Web Admin quando a regra de validacao de e-mail de cliente era aplicada para usuarios com perfil administrativo.

## Decisao
1. O `PortalConfig` passa a persistir `email_settings` (JSON) como configuracao central de e-mail no backend.
2. O Web Admin recebe a secao `Portal CMS > E-mail` para configurar SMTP e testar envio.
3. Foi criado endpoint administrativo para teste:
   - `POST /api/v1/portal/admin/config/test-email/`
4. A regra de autenticacao passa a ser explicitamente segmentada:
   - validacao obrigatoria de e-mail aplica-se somente ao fluxo de contas cliente;
   - usuarios administrativos/gestao (`ADMIN`, `FINANCEIRO`, `COZINHA`, `COMPRAS`, `ESTOQUE`, `is_staff`, `is_superuser`) nao sao bloqueados por falta de validacao de e-mail.

## Consequencias
- Beneficios:
  - configuracao de e-mail governada pelo Web Admin, sem alterar manualmente ambiente para cada ajuste;
  - diagnostico rapido de credenciais SMTP com botao de teste;
  - evita indisponibilidade operacional do Admin por regra de compliance do canal cliente.
- Trade-offs:
  - segredos SMTP ficam no banco (acesso restrito ao canal admin autenticado);
  - exige validacoes estritas no backend para evitar combinacoes invalidas (TLS/SSL/porta/e-mail).

## Implementacao
- Backend:
  - `PortalConfig.email_settings` (migration `0009`).
  - normalizacao e validacao de `email_settings` em `apps/portal/services.py` e `apps/portal/serializers.py`.
  - acao admin de teste em `apps/portal/views.py`.
  - envio de confirmacao de conta em `apps/accounts/services.py` passa a usar configuracao de e-mail do Portal com fallback seguro.
  - regra de login em `apps/accounts/serializers.py` refinada para excluir perfis administrativos do bloqueio de validacao de e-mail.
- Web Admin:
  - nova secao `E-mail` no modulo `Portal CMS` com campos SMTP, identidade de envio e botao de teste.

## Testes
- `npm run lint` e `npm run build` no `workspaces/web/admin`.
- `python manage.py check` e `python manage.py makemigrations --check` no backend.
- testes automatizados de backend preparados/atualizados para regra de login e e-mail, com execucao dependente de PostgreSQL ativo no ambiente.
