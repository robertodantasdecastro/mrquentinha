# Plano de Implementacao - Instalacao Hibrida (DEV + PROD) na maquina atual

Data: 02/03/2026
Status: EXECUTADO
Responsavel: Codex

## 1) Objetivo
Instalar e configurar o ambiente Mr Quentinha nesta maquina com:
- PostgreSQL local instalado e configurado;
- bancos separados para dados de exemplo (DEV) e dados reais (PROD);
- backend + frontends preparados para modo hibrido (rede local + DNS/subdominios oficiais);
- instalacao totalmente executada por `installdev.sh`, com checkpoint de continuidade.

## 2) Regras e restricoes aplicadas
- Sem Docker/containers.
- PostgreSQL local obrigatorio.
- Segregacao DEV/PROD obrigatoria (`mrquentinha_dev` e `mrquentinha_prod`).
- DNS/subdominios conforme memoria:
  - `www.mrquentinha.com.br`
  - `app.mrquentinha.com.br`
  - `admin.mrquentinha.com.br`
  - `api.mrquentinha.com.br`
  - `dev.mrquentinha.com.br`
- Nao salvar segredo em repositorio versionado.

## 3) Senhas e seguranca (proposta tecnica)
Solicitacao recebida: usar senha padrao da maquina em todas as necessidades locais.

Implementacao segura proposta:
- Guardar segredo somente em area local protegida (fora do Git):
  - `/home/ubuntu/.mrquentinha-secure/host-secrets.env`
  - permissoes `chmod 600`
- O workflow global do Codex tera apenas referencia ao caminho seguro e nome das variaveis, sem valor em texto puro.
- Variaveis previstas:
  - `MRQ_MACHINE_DEFAULT_SECRET`
  - `MRQ_DB_PASS`
  - `MRQ_SUDO_PASS_HINT` (opcional)

## 4) Parametros de continuidade (checkpoint)
- Arquivo de estado: `.runtime/install/hybrid_install_state.json`
- Log principal: `.runtime/install/hybrid_install.log`
- Semaforo de etapa atual: `.runtime/install/hybrid_install.current_step`
- Regra operacional: ao final de cada tarefa, atualizar estado para `completed|failed` com timestamp e evidencias.

## 5) Etapas de execucao (com atualizacao automatica de status)
1. Preparar seguranca local (arquivo de segredos fora do repo) e validar permissoes.
2. Ajustar `installdev.sh` para:
   - forcar Postgres local para provisionamento;
   - manter compatibilidade de DNS/subdominios oficiais;
   - separar `ALLOWED_HOSTS` entre DEV e PROD sem wildcard inseguro em PROD;
   - registrar checkpoint por etapa.
3. Executar `installdev.sh` com parametros de ambiente hibrido da documentacao.
4. Validar instalacao:
   - banco local ativo;
   - roles e bancos DEV/PROD criados;
   - migrations + seeds corretos por ambiente;
   - Nginx com hostnames oficiais;
   - smoke da stack (`smoke_stack_dev.sh`) usando IP atual.
5. Persistir memoria operacional:
   - atualizar `docs/memory/CHANGELOG.md`;
   - atualizar `docs/memory/DECISIONS.md`;
   - atualizar `docs/memory/RUNBOOK_DEV.md`;
   - atualizar `.agent/memory/CONTEXT_PACK.md` e `.agent/memory/TODO_NEXT.md`.

## 6) Criterios de aceite
- PostgreSQL local instalado e ativo via systemd.
- Bancos DEV/PROD separados e acessiveis.
- `.env.dev` e `.env.prod` gerados com parametros corretos de DNS/subdominios.
- Producao sem host permissivo indevido.
- Instalacao repetivel via `installdev.sh`.
- Checkpoint de continuidade funcionando para retomar de falha.

## 7) Modo de execucao
Plano aprovado e executado em 02/03/2026.
