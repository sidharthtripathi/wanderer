# Database migrations

Plain SQL, applied in lexical order. Numbered `NNNN_description.sql`.

Authoritative source of truth lives in [`docs/spec.md` §6.1](../../docs/spec.md). Migrations are derived from the spec — when the spec changes, add a new migration; never edit an applied one.

## Apply locally

```bash
# After docker compose -f infra/docker/docker-compose.yml up -d
psql postgresql://wanderer:wanderer@localhost:5432/wanderer \
  -f infra/migrations/0001_initial_schema.sql
```

In production we'll wire this through Alembic in `core-api`, but raw SQL keeps Slice-1 simple and reviewable.
