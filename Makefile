.PHONY: all build up down wait-for-app clean make-dev-env

all: up wait-for-app down

build:
	docker compose build

up:
	docker compose up --build -d

wait-for-app:
	@echo "Waiting for container 'app' to produce output files, then stopping 'mongodb' container"; 
	@while docker ps --filter "name=^app$$" --filter "status=running" --format "{{.Names}}" | grep -qx "app"; do \
		sleep 1; \
	done

down:
	docker compose down

make-dev-env:
	python3 -m venv .venv
	.venv/bin/python -m pip install -r python-docker-src/requirements.txt

inspect-containers:
	docker compose logs -f

checkmongoalive:
	@docker ps --filter "name=^mongodb$$" --filter "status=running" --format "{{.Names}}" | grep -qx "mongodb" || \
		(echo "Error: MongoDB container 'mongodb' is not running."; exit 1)

peek-database: checkmongoalive
	@docker exec -it mongodb mongosh --quiet --eval 'db.adminCommand({ listDatabases: 1 }).databases.filter(d => !["admin", "config", "local"].includes(d.name)).forEach(d => { print("\n=== DATABASE: " + d.name + " ==="); const database = db.getSiblingDB(d.name); database.getCollectionNames().forEach(c => { print("\n--- COLLECTION: " + c + " ---"); printjson(database.getCollection(c).find({}).toArray()); }); });'

full-clean-remove-volumes:
	docker compose down -v






