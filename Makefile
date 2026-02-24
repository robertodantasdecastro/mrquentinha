SHELL := /bin/bash

.PHONY: test lint format check

test:
	cd workspaces/backend && make test
	@if [[ -x workspaces/backend/.venv/bin/pytest ]]; then \
		echo "[make test] Rodando pytest no root com workspaces/backend/.venv/bin/pytest"; \
		workspaces/backend/.venv/bin/pytest; \
	elif command -v pytest >/dev/null 2>&1; then \
		echo "[make test] Rodando pytest no root com pytest do PATH"; \
		pytest; \
	else \
		echo "[make test] AVISO: pytest nao encontrado. Ative a venv em workspaces/backend/.venv"; \
	fi

lint:
	cd workspaces/backend && make lint

format:
	cd workspaces/backend && make format

check:
	cd workspaces/backend && python manage.py check
