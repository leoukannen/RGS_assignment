.PHONY: all build up down clean

all: up

build:
	docker compose build

up:
	docker compose up --build -d

down:
	docker compose down

inspect-containers:
	docker compose logs -f

full-clean-remove-volumes:
	docker compose down -v