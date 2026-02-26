# ADR-0004: LGPD operacional para finanças pessoais (exportação, auditoria e retenção)

## Status
Aceito

## Contexto
Após a entrega do domínio `personal_finance` (`T8.1.1`), faltava fechar requisitos operacionais
de LGPD para o MVP técnico: capacidade de exportar os dados do titular, registrar trilha de acesso
e aplicar política mínima de retenção para logs de auditoria.

## Decisão
- Expor endpoint autenticado `GET /api/v1/personal-finance/export/` para o usuário exportar os
  próprios dados pessoais (`accounts`, `categories`, `entries`, `budgets` e `audit_logs`).
- Criar modelo `PersonalAuditLog` para registrar eventos `LIST`, `RETRIEVE`, `CREATE`, `UPDATE`,
  `DELETE` e `EXPORT` no domínio pessoal.
- Expor endpoint autenticado `GET /api/v1/personal-finance/audit-logs/` para consulta da trilha
  do próprio usuário.
- Implementar comando operacional `purge_personal_audit_logs` com política padrão de retenção de
  `730` dias para logs de auditoria.

## Consequências
- Positivas:
  - melhora rastreabilidade de acesso e mudanças em dados pessoais.
  - entrega mecanismo prático de portabilidade/exportação no escopo MVP.
  - reduz crescimento indefinido de logs com rotina de retenção definida.
- Trade-offs:
  - aumento de volume de escrita por auditoria em cada ação relevante.
  - necessidade de agendamento operacional periódico para execução do comando de purge.

## Alternativas consideradas
- Registrar auditoria apenas em logs de aplicação (sem persistência no banco).
- Fazer exportação somente via suporte manual/administrativo.
- Aplicar retenção apenas por política documental, sem comando operacional dedicado.
