.PHONY: test lint format check

test:
	cd workspaces/backend && make test

lint:
	cd workspaces/backend && make lint

format:
	cd workspaces/backend && make format

check:
	cd workspaces/backend && python manage.py check
