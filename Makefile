.PHONY: infra-up infra-down migrate run-core-api run-ai-orchestrator lint

infra-up:
	docker compose -f infra/docker/docker-compose.yml up -d

infra-down:
	docker compose -f infra/docker/docker-compose.yml down

migrate:
	@psql "postgresql://wanderer:wanderer@localhost:5432/wanderer" \
		-f infra/migrations/0001_initial_schema.sql

run-core-api:
	cd backend/core-api && uv run uvicorn app.main:app --reload --port 8080

run-ai-orchestrator:
	cd backend/ai-orchestrator && uv run uvicorn app.main:app --reload --port 8081

lint:
	cd backend/core-api && uv run ruff check . || true
	cd backend/ai-orchestrator && uv run ruff check . || true
