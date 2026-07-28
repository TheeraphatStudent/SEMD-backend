ifeq ($(OS),Windows_NT)
SHELL := C:/Program Files/Git/bin/bash.exe
else
SHELL := bash
endif
.ONESHELL:
.PHONY: help setup config install start prod worker clean test typecheck lint check openapi

help:
	@echo "make setup     - bootstrap config files (backend.ini, redis.conf, docker/postgres.env) and install deps via uv"
	@echo "make start     - build and run the Docker/Podman stack from docker/docker-compose.yaml"
	@echo "make prod      - run the production server (uv run python main.py prod)"
	@echo "make worker    - run the ML result Redis worker (uv run python -m workers.prediction_worker)"
	@echo "make test      - run the unittest suite (tests/unit)"
	@echo "make typecheck - run mypy (baseline config, see pyproject.toml)"
	@echo "make lint      - run ruff check"
	@echo "make openapi   - regenerate openapi.yaml from the live app"
	@echo "make check     - test + typecheck + lint"
	@echo "make clean     - remove .venv and __pycache__ directories"

setup: config install

config:
	cp -n config/redis.example.conf config/redis.conf
	cp -n config/backend.example.ini config/backend.ini
	REDIS_PASSWORD=$$(grep -A10 '^\[REDIS\]' config/backend.ini | grep '^PASSWORD' | head -1 | cut -d'=' -f2 | xargs)
	REDIS_ROOT_PASSWORD=$$(grep -A10 '^\[REDIS\]' config/backend.ini | grep '^ROOT_PASSWORD' | head -1 | cut -d'=' -f2 | xargs)
	POSTGRES_USER=$$(grep -A10 '^\[POSTGRESQL\]' config/backend.ini | grep '^USER' | head -1 | cut -d'=' -f2 | xargs)
	POSTGRES_PASSWORD=$$(grep -A10 '^\[POSTGRESQL\]' config/backend.ini | grep '^PASSWORD' | head -1 | cut -d'=' -f2 | xargs)
	POSTGRES_DB=$$(grep -A10 '^\[POSTGRESQL\]' config/backend.ini | grep '^DB' | head -1 | cut -d'=' -f2 | xargs)
	sed -i "s/<master-password>/$$REDIS_ROOT_PASSWORD/g" config/redis.conf
	sed -i "s/<password>/$$REDIS_PASSWORD/g" config/redis.conf
	printf 'POSTGRES_USER=%s\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=%s\n' "$$POSTGRES_USER" "$$POSTGRES_PASSWORD" "$$POSTGRES_DB" > docker/postgres.env

install:
	test -f pyproject.toml || uv init --no-readme --python 3.12
	uv add -r requirements.txt
	uv sync

start: stop
	podman compose -f docker/docker-compose.yaml up -d --build --remove-orphans

stop:
	podman compose -f docker/docker-compose.yaml down --remove-orphans

prod:
	uv run python main.py prod

worker:
	uv run python -m workers.prediction_worker

test:
	uv run python -m unittest discover -s tests/unit -p "test_*.py"

typecheck:
	uv run mypy .

lint:
	uv run ruff check .

openapi:
	uv run python -c "import yaml, main; open('openapi.yaml', 'w').write(yaml.dump(main.app.openapi(), sort_keys=False))"

check: test typecheck lint

clean:
	rm -rf .venv
	find . -type d -name '__pycache__' -exec rm -rf {} +
