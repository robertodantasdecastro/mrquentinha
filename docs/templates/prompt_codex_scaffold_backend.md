# Prompt — Scaffold Backend (Django + DRF + Postgres)

Tarefa: criar o esqueleto do backend seguindo `AGENTS.md`.

Entregas:
1) Projeto Django configurado (settings por ambiente)
2) DRF instalado e `/api/v1/health`
3) Conexão Postgres via `.env` (criar `.env.example`)
4) Estrutura por domínios (apps vazios): accounts, catalog, inventory, procurement, orders, finance, ocr_ai
5) Ferramentas de qualidade: ruff + black + pytest (config inicial)
6) README de execução local

DoD:
- `python manage.py check` ok
- `pytest` ok (mesmo que só smoke tests)
- sem Docker
- docs atualizadas em `docs/memory/CHANGELOG.md`
