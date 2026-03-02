# Guia de instalacao AWS (infra pre-configurada) + bancos separados (dev/prod)

Data: 02/03/2026  
Perfil: usuario avancado AWS

## 1) Pre-requisitos no AWS Console (feito pelo usuario)
1. Criar uma instancia EC2 com acesso SSH via chave `.pem`.
2. Configurar o Route 53 apontando `www.mrquentinha.com.br` para a EC2.
3. Security Group liberando portas: `22`, `80`, `443`, `8000`.
4. Acessar a instancia via SSH e clonar o repo:
   ```bash
   git clone https://github.com/robertodantasdecastro/mrquentinha.git
   cd mrquentinha
   ```
5. Configurar acesso ao GitHub (caso use fork/permissoes de desenvolvimento).

## 2) Objetivo da separacao DEV/PROD
- DEV: banco com dados de testes e configuracoes atuais (snapshot do ambiente local).
- PROD: banco zerado, apenas com defaults minimos de sistema, configurado via Web Admin.
- Garantia: dados de DEV nunca aparecem em PRODUCAO.

## 3) Exportar dados DEV do ambiente local (antes de subir na EC2)
No ambiente local, gere um dump do banco atual:
```bash
PGPASSWORD=SUASENHA pg_dump -Fc -U mrq_user -h localhost -p 5432 mrquentinha > /tmp/mrq_dev.dump
```
Envie para a EC2:
```bash
scp -i sua-chave.pem /tmp/mrq_dev.dump ubuntu@IP_DA_EC2:/tmp/mrq_dev.dump
```

## 4) Executar instalacao DEV/PROD na EC2
Na EC2 (dentro do repo):
```bash
./installdev.sh
```
Opcional (para restaurar o dump automaticamente):
```bash
MRQ_DEV_DB_DUMP_PATH=/tmp/mrq_dev.dump ./installdev.sh
```

O script:
- Instala dependencias (Python, Node, Postgres).
- Cria 2 bancos separados: `mrquentinha_dev` e `mrquentinha_prod`.
- Gera `.env.dev` e `.env.prod` com chaves distintas.
- Deixa `.env` apontando para DEV.
- Restaura dump DEV (ou usa seed DEMO se dump nao for informado).
- Prepara PROD com migrations + `seed_portal_default`.

## 5) Como alternar entre DEV e PROD
DEV:
```bash
cd workspaces/backend
ln -sf .env.dev .env
```
PROD:
```bash
cd workspaces/backend
ln -sf .env.prod .env
python manage.py migrate
python manage.py seed_portal_default
```

## 6) Atualizacao da aplicacao (rotina)
Sempre que atualizar o repo:
```bash
git pull
cd workspaces/backend
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

Para frontends:
```bash
cd workspaces/web/portal && npm install
cd ../client && npm install
cd ../admin && npm install
```

## 7) Preparar Web Admin para instalacao (PROD)
1. Garanta que o banco PROD esta ativo (`.env` -> `.env.prod`).
2. Execute `python manage.py seed_portal_default`.
3. Inicie o backend e o Admin:
   ```bash
   ./scripts/start_backend_dev.sh
   ./scripts/start_admin_dev.sh
   ```
4. Acesse `Instalacao / Deploy` no Web Admin e conclua:
   - dados da empresa
   - pagamento
   - dominios/SSL

## 8) Operacao rapida
```bash
./scripts/ops_dashboard.sh --auto-start
```
Permite iniciar/parar backend, admin, portal, client e agora o Postgres local.
