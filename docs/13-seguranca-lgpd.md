# Segurança e LGPD (mínimo necessário desde o início)

## Dados coletados
- cliente: nome, e-mail, telefone (opcional), histórico de pedidos e pagamentos
- interno: e-mail, perfis, ações (auditoria)
- financeiro: contas, despesas e receitas

## Boas práticas
- minimizar dados pessoais
- consentimento e finalidade clara (termos)
- logs sem vazar dados sensíveis
- senhas: se houver login local, usar hashing forte (Django já faz)

## Acesso
- RBAC obrigatório
- segregação de funções (financeiro não precisa editar cardápio, por exemplo)

## Retenção
- definir política de retenção de logs e dados (futuro)
- permitir exportação/remoção conforme necessário (fase 2)

## Checklist de segurança por release
- [ ] endpoints protegidos
- [ ] validação de input
- [ ] rate limiting (quando exposto)
- [ ] backups verificados

## Atualizacao 26/02/2026 (T8.0.1)
- Discovery de segregacao de financas pessoais concluido em:
  - `docs/memory/T8_0_1_FINANCAS_PESSOAIS_DISCOVERY.md`
  - `docs/adr/0003-segregacao-financas-pessoais.md`
- Diretriz principal:
  - manter `finance` (operacional) separado de `personal_finance` (pessoal), com ownership
    obrigatorio por usuario e API dedicada.
- Implementacao tecnica concluida em `T8.1.1`:
  - app backend `personal_finance` publicado com filtros por `request.user` em todos os endpoints.
  - validacoes de ownership em serializers/services para impedir acesso cruzado entre usuarios.
- Implementacao operacional concluida em `T8.1.2`:
  - endpoint `GET /api/v1/personal-finance/export/` para exportacao dos dados pessoais do proprio usuario.
  - trilha de auditoria em `PersonalAuditLog` para eventos de leitura/escrita/exportacao.
  - comando `python manage.py purge_personal_audit_logs --days 730` para aplicar retencao de logs.
