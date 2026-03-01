# Guia de Testes Manuais - Instalacao / Deploy

Data: 01/03/2026  
Escopo: modulo `Instalacao / Deploy` do Web Admin (`/modulos/instalacao-deploy`)

## 1. Objetivo
Validar, de ponta a ponta, o comportamento do assistente de instalacao/deploy em todos os cenarios suportados:
- local;
- SSH remoto;
- AWS;
- Google Cloud (validacao basica de conectividade);
- bloqueios de pre-requisitos em producao;
- seguranca de dados sensiveis;
- operacao de jobs (inicio, status, cancelamento e logs).

## 2. Pre-condicoes
- Backend, Admin Web e banco ativos.
- Usuario com perfil `ADMIN`.
- Massa minima de dados carregada no `PortalConfig`.
- Para cenarios cloud/ssh:
  - conectividade de rede disponivel no host do backend;
  - CLIs instaladas conforme cenario (`aws` ou `gcloud`).

## 3. Comandos de validacao automatizada (antes dos testes manuais)
No backend (`workspaces/backend`):

```bash
source .venv/bin/activate
ruff check src/apps/portal/services.py src/apps/portal/views.py tests/test_portal_services.py tests/test_portal_api.py
pytest tests/test_portal_services.py tests/test_portal_api.py
```

No admin (`workspaces/web/admin`):

```bash
npm run lint
npm run build
```

No root do projeto:

```bash
bash scripts/check_installer_workflow.sh --check
```

## 4. Matriz de cenarios manuais

### Cenario A1 - Local DEV (sucesso)
1. Abrir `Instalacao / Deploy`.
2. Passo `Modo`: selecionar `dev`, `vm`, `target=local`.
3. Validar etapa e salvar draft.
4. Ir para `Execucao` e iniciar job.
5. Confirmar:
   - job criado;
   - status evolui para `running` e depois `succeeded` ou `finished`;
   - logs exibidos no painel.

### Cenario A2 - Producao sem pre-requisitos (bloqueio)
1. Configurar `mode=prod`.
2. Manter DNS/pagamento incompletos.
3. Tentar iniciar job.
4. Confirmar bloqueio com mensagem de pre-requisito e abertura do modal.

### Cenario A3 - Producao com pre-requisitos completos (liberado)
1. Completar DNS e gateway no modal.
2. Validar novamente.
3. Confirmar `prerequisites.ready=true`.
4. Iniciar job e conferir resumo normal.

### Cenario B1 - SSH com chave (sucesso)
1. `target=ssh`, `auth_mode=key`, preencher host/usuario/chave/repo_path.
2. Validar etapa.
3. Iniciar job.
4. Confirmar:
   - `connectivity_checks` inclui `ssh_connectivity`;
   - comando mascarado em preview;
   - logs e status atualizam no polling.

### Cenario B2 - SSH com senha sem senha (erro)
1. `auth_mode=password` sem preencher senha.
2. Validar.
3. Confirmar erro de validacao obrigando senha.

### Cenario B3 - SSH com auto clone sem git URL (erro)
1. Marcar `auto_clone_repo=true` sem `git_remote_url`.
2. Validar.
3. Confirmar erro de validacao.

### Cenario C1 - AWS com `profile` (sucesso de validacao)
1. `target=aws`, `provider=aws`, `auth_mode=profile`.
2. Informar `region` e, opcionalmente, `profile_name`.
3. Acionar `Validar AWS`.
4. Confirmar retorno com:
   - conectividade `aws_connectivity` OK;
   - checks de `aws_route53`, `aws_ec2_instance`, `aws_elastic_ip`, `aws_codedeploy`;
   - bloco de custos estimados.

### Cenario C2 - AWS com `access_key` (sucesso de validacao)
1. `auth_mode=access_key`.
2. Informar `access_key_id`, `secret_access_key` (runtime) e opcional `session_token`.
3. Acionar `Validar AWS`.
4. Confirmar sucesso e exibicao de custo/checks.
5. Salvar draft e recarregar pagina.
6. Confirmar que:
   - `secret_access_key` nao reaparece;
   - `session_token` nao reaparece.

### Cenario C3 - AWS sem CLI (erro esperado)
1. Executar em ambiente sem `aws` CLI.
2. Acionar `Validar AWS`.
3. Confirmar mensagem de erro orientando instalacao da CLI.

### Cenario C4 - AWS com Cost Explorer sem permissao
1. Conta AWS sem permissao `ce:GetCostAndUsage`.
2. Acionar `Validar AWS`.
3. Confirmar:
   - validacao principal segue OK (quando STS/IAM ok);
   - custo MTD aparece indisponivel com orientacao de permissao.

### Cenario D1 - GCP conectividade basica
1. `target=gcp`, preencher `region`.
2. Validar e iniciar plano.
3. Confirmar check de conectividade com `gcloud auth list`.

### Cenario E1 - Cancelamento de job
1. Iniciar job local ou SSH.
2. Acionar `Cancelar job`.
3. Confirmar status final `canceled`.

## 5. Checklist de aceite
- Validacoes por etapa funcionam com mensagens claras.
- Bloqueios de pre-requisito em producao impedem execucao.
- Dados sensiveis nao ficam persistidos no draft/job.
- Jobs exibem status, logs e checks de conectividade.
- AWS mostra custo estimado e tentativa de custo real MTD.
- Navegacao do modulo funciona em todos os templates do Web Admin.

## 6. Evidencias recomendadas por rodada
- Captura da tela de cada cenario com timestamp.
- JSON de resposta dos endpoints:
  - `/api/v1/portal/admin/config/installer-wizard-validate/`
  - `/api/v1/portal/admin/config/installer-cloud/aws/validate/`
  - `/api/v1/portal/admin/config/installer-jobs/<job_id>/status/`
- Log resumido do job final (ultimas linhas + status).
