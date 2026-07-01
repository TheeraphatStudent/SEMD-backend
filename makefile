ifeq ($(OS),Windows_NT)
SHELL := C:/Program Files/Git/bin/bash.exe
else
SHELL := bash
endif
.ONESHELL:
.PHONY: help setup config install start prod worker clean

help:
	@echo "make setup   - bootstrap config files (backend.ini, redis.conf, database/.env) and install deps via uv"
	@echo "make start   - run the dev server (uv run fastapi dev main.py)"
	@echo "make prod    - run the production server (uv run python main.py prod)"
	@echo "make worker  - run the ML result Redis worker (uv run python -m workers.prediction_worker)"
	@echo "make clean   - remove .venv and __pycache__ directories"

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
	printf 'POSTGRES_USER=%s\nPOSTGRES_PASSWORD=%s\nPOSTGRES_DB=%s\n' "$$POSTGRES_USER" "$$POSTGRES_PASSWORD" "$$POSTGRES_DB" > database/.env
	sed -i '/^[[:space:]]*environment:/d' database/docker-compose.database.yaml
	sed -i '/^[[:space:]]*POSTGRES_USER:/d' database/docker-compose.database.yaml
	sed -i '/^[[:space:]]*POSTGRES_PASSWORD:/d' database/docker-compose.database.yaml
	sed -i '/^[[:space:]]*POSTGRES_DB:/d' database/docker-compose.database.yaml
	sed -i '/^[[:space:]]*env_file:/{N;d;}' database/docker-compose.database.yaml
	sed -i '/^[[:space:]]*- 5433:5432/a\    env_file:\n      - .env' database/docker-compose.database.yaml
	sed -i 's/-U", "example"/-U", "'"$$POSTGRES_USER"'", "-d", "'"$$POSTGRES_DB"'"/' database/docker-compose.database.yaml

install:
	test -f pyproject.toml || uv init --no-readme --python 3.12
	uv add -r requirements.txt
	uv sync

start:
	uv run fastapi dev main.py

prod:
	uv run python main.py prod

worker:
	uv run python -m workers.prediction_worker

clean:
	rm -rf .venv
	find . -type d -name '__pycache__' -exec rm -rf {} +
