.PHONY: install install-dev check migrate runserver test lint format

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

check:
	python manage.py check

migrate:
	python manage.py migrate

runserver:
	python manage.py runserver 0.0.0.0:8000

test:
	pytest

lint:
	ruff check .
	black --check .

format:
	ruff check . --fix
	black .
