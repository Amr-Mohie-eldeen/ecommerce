# Catalog API

Clean FastAPI service using Ports-and-Adapters with Postgres, Redis, and OpenSearch.

Routes (v1):
- POST `/products` — create product, emit `ProductUpdated`
- GET `/products/{id}` — fetch product (Redis cached)
- GET `/search` — search via OpenSearch (cached)

Architecture
- Domain models decoupled from I/O; adapters for DB (SQLAlchemy async), Redis, OpenSearch, and Kafka events.
- App factory initializes DB/Redis and wires routes.

Environment
- `PORT` (default 8001)
- `DB_URL` (e.g., `postgresql+asyncpg://app:postgres@postgres:5432/appdb`)
- `REDIS_URL` (e.g., `redis://redis:6379/0`)
- `OPENSEARCH_URL`, `ENABLE_KAFKA`, `TOPIC_PRODUCT_UPDATED`
- Shared OTEL/others inherited from root `.env`.

Run locally
- Start deps: `make local-up`
- Health checks: `make local-health`
- Seed OpenSearch/SR: `make seed-data`

Notes
- If DB/Redis are unavailable, the app falls back to in-memory repo and no-op cache for dev/test convenience.
