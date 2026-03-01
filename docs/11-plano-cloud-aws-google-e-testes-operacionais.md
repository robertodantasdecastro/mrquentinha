# Plano de implementacao cloud (AWS primeiro)

Data: 01/03/2026  
Status: planejado para execucao incremental

## 1. Objetivo
Implementar no Web Admin um fluxo guiado de instalacao/deploy em cloud, com foco inicial em AWS, incluindo:
- validacao de pre-requisitos tecnicos e de seguranca;
- configuracao assistida de credenciais e conectividade;
- provisionamento orientado de recursos (DNS, EC2, IP, deploy);
- transparencia de custos atuais e projetados durante o wizard.

O mesmo padrao sera replicado depois para Google Cloud.

## 2. Escopo da fase atual (prioridade)
1. Provider cloud no instalador: `AWS` ou `Google Cloud`.
2. Trilha completa inicial para `AWS`.
3. Custos exibidos no Web Admin por etapa (estimativa e/ou consumo real quando disponivel na conta).
4. Operacao guiada com confirmacoes explicitas antes de criar recursos cobraveis.

## 3. Principios obrigatorios
- Seguranca por padrao: menor privilegio (IAM), segredos mascarados e sem persistencia indevida.
- Modo assistido: nenhuma criacao destrutiva sem confirmacao do usuario administrador.
- Observabilidade: logs claros por job, checks de conectividade e status por servico.
- Custos visiveis: sempre mostrar impacto financeiro estimado antes de aplicar mudancas.

## 4. Plano AWS por fases

### Fase AWS-1: Base de credenciais e conectividade
- Adicionar no Web Admin area segura para credenciais AWS com dois modos:
  - Access key + secret (+ session token opcional).
  - Perfil/role assumida quando o host ja estiver autenticado.
- Validar credenciais com chamadas de leitura:
  - `sts:GetCallerIdentity`
  - `iam:ListAccountAliases` (opcional, para contexto visual)
- Regras de seguranca:
  - nunca persistir `secret_access_key` em texto puro;
  - permitir teste sem salvar;
  - registrar apenas metadados nao sensiveis (account id, arn, region valida).

### Fase AWS-2: Prerequisitos de infraestrutura no wizard
- Checklists automáticos e orientados para:
  - DNS em Route53 (zona hospedada e registros A/CNAME);
  - existencia/acesso de instancia EC2 alvo;
  - escolha de IP publico:
    - `Elastic IP` (recomendado para estabilidade)
    - IP dinamico (baixo custo inicial, maior risco operacional)
- Fluxo de decisao no Web Admin:
  - se recurso existe: validar e vincular.
  - se nao existe: exibir custo estimado e solicitar confirmacao para criar.

### Fase AWS-3: Provisionamento assistido de EC2 + rede
- Criacao guiada (quando necessario):
  - EC2 (tipo, AMI, disco, SG, key pair, user-data inicial).
  - Security Group minimo para `22/80/443` conforme ambiente.
  - Elastic IP opcional e associacao na instancia.
- Validacoes de runtime:
  - SSH reachability.
  - acesso outbound para instalar dependencias.
  - consistencia de regiao/zonas com recursos selecionados.

### Fase AWS-4: Deploy aplicacional com CodeDeploy (ou SSH fallback)
- Implementar no assistente:
  - preparo de artefato/repo e branch alvo;
  - estrategia de deploy com rollback;
  - health-check pos deploy.
- Se CodeDeploy nao estiver habilitado, manter fallback por SSH com trilha auditavel.
- Exibir no job:
  - etapa atual,
  - logs por fase,
  - tempo e status final.

### Fase AWS-5: Custos no Web Admin (estimativa e consumo)
- Fontes de custo:
  - AWS Price List API (estimativa por servico/sku).
  - Cost Explorer (consumo real quando habilitado na conta).
- Exibir no wizard:
  - custo mensal estimado da configuracao em andamento;
  - custo incremental ao criar novo recurso;
  - faixa prevista para cenario inicial `< 20 clientes` e cenario de crescimento.
- Servicos minimos com custo exibido:
  - EC2, EBS, Elastic IP, Route53 e transferencia de dados.

### Fase AWS-6: Operacao, auditoria e protecoes
- Auditoria administrativa das acoes cloud (quem executou, quando, recurso afetado).
- Dry-run para operacoes de criacao/alteracao.
- Confirmacao dupla para itens de maior impacto financeiro.
- Relatorio de postura final apos instalacao:
  - recursos criados,
  - custos estimados,
  - pendencias de hardening.

## 5. Modelo inicial de recomendacao de custo (ate 20 clientes)
Perfil recomendado para inicio:
- 1 instancia EC2 pequena com disco EBS enxuto;
- Elastic IP para estabilidade de DNS;
- Route53 para zona e registros do dominio;
- backup de banco e snapshots com periodicidade definida.

Observacoes:
- IP dinamico reduz custo inicial, mas aumenta risco de indisponibilidade apos restart/troca de IP.
- Elastic IP tende a ser a opcao mais previsivel para ambiente produtivo com DNS publico.
- custos exatos dependem de regiao, classe de instancia, disco, trafego e horas de uso.

## 6. Backlog futuro relacionado

### 6.1 Paridade com Google Cloud
- Repetir o mesmo contrato funcional do AWS no wizard:
  - credenciais,
  - prerequisitos,
  - provisionamento,
  - deploy,
  - custos.
- Implementar mapeamento equivalente:
  - DNS, VM, IP estatico, pipeline de deploy, observabilidade.
- Garantir UX unificada para alternar `AWS` x `Google Cloud` sem quebrar o fluxo.

### 6.2 Testes operacionais guiados (fim a fim)
- Criar campanha formal de testes operacionais em todos os processos:
  - validacao de credenciais,
  - checks de pre-requisito,
  - provisionamento,
  - deploy,
  - rollback,
  - custos,
  - auditoria.
- Definir roteiro com cenarios:
  - sucesso completo,
  - credencial invalida,
  - falta de permissao IAM,
  - recurso inexistente,
  - custo acima de limite esperado,
  - falha de deploy com rollback.
- Publicar relatorio de ajustes/correcoes por rodada.

## 7. Dependencias para execucao com autonomia parcial
Para executar totalmente a automacao cloud, sera necessario do usuario/operacao:
- conta AWS ativa com faturamento habilitado;
- politicas IAM e permissoes minimas aprovadas;
- definicao de dominio/zona DNS de producao;
- escolha da regiao cloud principal;
- limites de custo mensal (budget) por ambiente.

Sem esses itens, conseguimos implementar a estrutura tecnica, validacoes e dry-run, mas nao a automacao completa em ambiente real.

## 8. Entregaveis da proxima iteracao
1. Wizard AWS com credenciais seguras e checks de conectividade.
2. Bloco de pre-requisitos AWS (Route53, EC2, Elastic IP, SSH) com decisoes guiadas.
3. Primeira versao de painel de custos (estimativa) no Web Admin.
4. Backlog tecnico estruturado para Google Cloud.
5. Suite de testes operacionais guiados para a trilha cloud.
