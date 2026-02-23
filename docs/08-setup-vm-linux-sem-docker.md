# Setup da VM Linux (sem Docker)

> Objetivo: preparar um ambiente offline replicável para dev e depois para EC2.

## 1) Sistema operacional sugerido
- Ubuntu Server LTS (22.04 ou 24.04)

## 2) Pacotes base
Instalar:
- Git
- Python 3.12+ (ou 3.11)
- Node 20 LTS+
- PostgreSQL 15+
- Build tools (gcc, make) e libs comuns

## 3) Backend (Django)
Sugestão de setup:
- criar venv: `python -m venv .venv`
- ativar: `source .venv/bin/activate`
- instalar deps (pip/poetry — escolha um padrão e mantenha)

Comandos padrão (a definir no scaffold):
- `python manage.py migrate`
- `python manage.py runserver`

## 4) Banco (PostgreSQL)
- criar usuário e banco do projeto
- definir `DATABASE_URL` no `.env`

## 5) Web (React/Next)
- `npm install`
- `npm run dev`

## 6) Mobile (React Native)
- Expo (mais rápido no MVP) ou Bare
- Android: gerar APK para pilotos
- iOS: planejar TestFlight para distribuição

## 7) Padrões de execução
- Backend em `workspaces/backend/`
- Web em `workspaces/web/`
- Mobile em `workspaces/mobile/`

## 8) Checklist final do ambiente
- [ ] `psql` conecta
- [ ] backend sobe e faz healthcheck
- [ ] web sobe e consome `/api/v1/health`
- [ ] mobile autentica e lista cardápio
