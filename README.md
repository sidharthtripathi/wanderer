# Wanderer

> An AI-powered, community-driven companion for spontaneous travel.

See [`docs/product_doc.md`](docs/product_doc.md) for product intent, [`docs/spec.md`](docs/spec.md) for the engineering spec.

## Repo layout

```
android/          Android app (Kotlin + Jetpack Compose)
backend/
  core-api/         Python/FastAPI — auth, community, subscription
  ai-orchestrator/  Python/FastAPI — Gemini orchestration, memory, persona
  realtime-edge/    Go — WebSocket hub, GPS ingest, narration loop
infra/
  migrations/       SQL migrations
  docker/           local dev compose, configs
docs/             product + spec
scripts/          one-off operational scripts
```

## Local dev quickstart

```bash
# Infrastructure (Postgres+PostGIS, Qdrant, Redis)
docker compose -f infra/docker/docker-compose.yml up -d

# Run a migration
make migrate

# Backend services (in separate terminals)
make run-core-api
make run-ai-orchestrator
make run-realtime-edge

# Android: open ./android in Android Studio
```

See [`docs/spec.md` §14](docs/spec.md) for the build sequencing.
