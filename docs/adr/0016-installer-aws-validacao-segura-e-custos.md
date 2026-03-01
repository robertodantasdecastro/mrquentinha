# ADR 0016: Assistente AWS com validacao segura e visibilidade de custos

- Data: 01/03/2026
- Status: aceito
- Contexto:
  - A trilha `T9.2.7-A5-A2` exige evoluir o modulo `Instalacao / Deploy` para cloud AWS com fluxo guiado no Web Admin.
  - Era necessario adicionar validacao tecnica e de seguranca sem persistir segredos AWS em texto puro no `PortalConfig`.
  - Tambem era necessario expor custo estimado e custo real (quando permitido) durante a configuracao cloud.

## Decisao
- Expandir o contrato do `draft.cloud` no instalador para AWS com:
  - modo de autenticacao (`profile` ou `access_key`);
  - parametros de infraestrutura (Route53, EC2, Elastic IP, CodeDeploy, EBS).
- Introduzir endpoint administrativo dedicado:
  - `POST /api/v1/portal/admin/config/installer-cloud/aws/validate/`
  - retorno com:
    - conectividade AWS (STS/IAM),
    - checks de pre-requisito (Route53, EC2, Elastic IP, CodeDeploy),
    - custo mensal estimado da configuracao,
    - snapshot de custo MTD via Cost Explorer (quando permissoes permitirem).
- Aplicar politica de seguranca:
  - `secret_access_key` e `session_token` nunca sao persistidos no `installer_settings` nem em payload final de jobs;
  - validacao e execucao usam segredo apenas em runtime.
- Integrar a validacao AWS no UI do wizard (passo `Infraestrutura`), com painel de resultado e bloco de custos.

## Consequencias
- O operador consegue validar credenciais e infraestrutura AWS no proprio Web Admin antes de qualquer provisionamento.
- O assistente passa a mostrar impacto financeiro estimado com maior transparencia operacional.
- A automacao de provisionamento completo AWS continua como proxima fase; esta entrega foca validacao segura + decisao orientada por custo.
- Para consumo real de custo MTD, a conta AWS precisa permitir `ce:GetCostAndUsage`.
