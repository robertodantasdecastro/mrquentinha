# Backend Mr Quentinha (Django + DRF)

## Estrutura adotada
Foi utilizado o padrao `src/` para manter separacao clara entre codigo da aplicacao e arquivos de infraestrutura:

- `manage.py`: entrada do Django
- `src/config/`: configuracao principal (urls, wsgi/asgi, settings)
- `src/config/settings/`: separacao por ambiente (`dev` e `prod`)
- `src/apps/`: apps de dominio
- `tests/`: testes automatizados de integracao/API

## Apps de dominio criados
- `accounts`
- `catalog`
- `inventory`
- `procurement`
- `orders`
- `finance`
- `ocr_ai`

## Requisitos
- Python 3.11+
- PostgreSQL 15+

## Setup local
1. Entrar na pasta do backend:
   ```bash
   cd workspaces/backend
   ```
2. Criar/ativar virtualenv:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Instalar dependencias:
   ```bash
   pip install -r requirements-dev.txt
   ```
4. Configurar ambiente:
   ```bash
   cp .env.example .env
   ```
5. Ajustar `DATABASE_URL` no `.env` para seu PostgreSQL.

## Comandos principais
- Verificacao de configuracao Django:
  ```bash
  python manage.py check
  ```
- Aplicar migracoes:
  ```bash
  python manage.py migrate
  ```
- Subir servidor local:
  ```bash
  python manage.py runserver
  ```
- Rodar testes:
  ```bash
  pytest
  ```

## Qualidade (ruff + black + pytest)
Com Makefile:

- Lint:
  ```bash
  make lint
  ```
- Testes:
  ```bash
  make test
  ```
- Formatar codigo:
  ```bash
  make format
  ```

## Endpoint de health
- `GET /api/v1/health`
- Resposta esperada:
  ```json
  { "status": "ok", "app": "mrquentinha", "version": "v1" }
  ```
