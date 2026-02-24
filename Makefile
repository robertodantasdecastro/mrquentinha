SHELL := /bin/bash

BACKEND_DIR := workspaces/backend
BACKEND_VENV_ACTIVATE := $(BACKEND_DIR)/.venv/bin/activate

.PHONY: test lint format check

define require_backend_venv
@if [[ ! -f "$(BACKEND_VENV_ACTIVATE)" ]]; then  echo "[make] ERRO: venv nao encontrada em $(BACKEND_VENV_ACTIVATE)";  echo "[make] Crie e instale deps: cd $(BACKEND_DIR) && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements-dev.txt";  exit 1;  fi
endef

test:
	$(call require_backend_venv)
	cd $(BACKEND_DIR) && . .venv/bin/activate && make test

lint:
	$(call require_backend_venv)
	cd $(BACKEND_DIR) && . .venv/bin/activate && make lint

format:
	$(call require_backend_venv)
	cd $(BACKEND_DIR) && . .venv/bin/activate && make format

check:
	$(call require_backend_venv)
	cd $(BACKEND_DIR) && . .venv/bin/activate && python manage.py check
