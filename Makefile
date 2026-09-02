.PHONY: all build up down clean make-dev-env

all: up

build:
	docker compose build

up:
	docker compose up --build -d

down:
	docker compose down

make-dev-env:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r python-docker-src/requirements.txt

inspect-containers:
	docker compose logs -f

full-clean-remove-volumes:
	docker compose down -v