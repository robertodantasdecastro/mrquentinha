# GLOBAL RULE - Mr Quentinha

Regra-mae do projeto. Este arquivo deve ser lido antes de qualquer acao tecnica.

## 1) Mapa do repositorio
- `AGENTS.md`: regras principais do projeto.
- `docs/`: documentacao funcional e tecnica.
  - `docs/memory/`: memoria viva (`PROJECT_STATE`, `DECISIONS`, `CHANGELOG`, `RUNBOOK_DEV`).
- `scripts/`: automacoes de dev (`start_*.sh`, `smoke_*.sh`, `seed_demo.sh`, `session.sh`).
- `workspaces/backend/`: API Django/DRF + PostgreSQL.
- `workspaces/web/portal/`: frontend portal institucional (porta 3000).
- `workspaces/web/client/`: frontend cliente web (porta 3001).
- `workspaces/web/ui/`: Design System compartilhado (componentes/template/tokens).
- `.agent/`: regras operacionais, workflows, prompts e memoria auxiliar.
- `.antigravity/`: regras globais do ambiente Antigravity.

## 2) Portas e URLs locais
- Backend API: `http://127.0.0.1:8000`
- Portal: `http://127.0.0.1:3000`
- Client: `http://127.0.0.1:3001`

## 3) Scripts principais e quando usar
- `scripts/start_backend_dev.sh`: subir backend (migrate + runserver).
- `scripts/start_portal_dev.sh`: subir portal Next em dev.
- `scripts/start_client_dev.sh`: subir client Next em dev.
- `scripts/smoke_stack_dev.sh`: validacao ponta a ponta backend + portal + client + seed.
- `scripts/smoke_client_dev.sh`: validacao rapida do client.
- `scripts/seed_demo.sh`: carga idempotente de dados DEMO.
- `scripts/session.sh`: atalho de sessao (`start|continue|save|qa`).

## 4) Fontes obrigatorias de regra/memoria/workflows
- `AGENTS.md`
- `docs/memory/*`
- `.agent/workflows/*`
- `.agent/prompts/*`
- `.agent/rules/*`
- `.agent/memory/*`
- `.antigravity/*`

## 5) Padrao backend (obrigatorio)
- Estrutura por camada: `services.py`, `selectors.py`, `serializers.py`, `views.py`, `urls.py`, `tests`.
- Regra de negocio concentrada em service layer.
- Query e leitura concentradas em selectors.
- Toda mudanca de comportamento deve vir com teste.

## 6) Padrao frontend (obrigatorio)
- Reutilizar `workspaces/web/ui`.
- Usar `TemplateProvider` e componentes compartilhados.
- Layout clean, responsivo e consistente.
- Evitar hardcode de conteudo operacional; consumir API sempre que aplicavel.

## 7) Regras de git e entrega
- Commits pequenos e revisaveis.
- Em mudancas grandes: preferir 2 commits (implementacao + docs/memoria), quando fizer sentido.
- Atualizar sempre `docs/memory/CHANGELOG.md` e `docs/memory/PROJECT_STATE.md` quando houver impacto operacional.
- Nao usar mensagens de commit vagas (`WIP`, `tmp`, `fixes`).

## 8) Regra de segredos (inegociavel)
- Valores reais ficam somente em `.env` local (gitignored).
- Repositorio versiona somente `.env.example` com placeholders.
- Nunca registrar senhas/chaves/tokens reais em codigo, docs, commits, logs ou prompts.
