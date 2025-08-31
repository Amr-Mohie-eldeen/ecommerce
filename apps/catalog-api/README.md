# Catalog API

Routes (v1):
- POST `/products`
- GET `/products/{id}`
- GET `/search`

Environment
- `PORT` (default 8001)
- Inherit shared vars from root `.env` (`DB_URL`, `REDIS_URL`, `KAFKA_BOOTSTRAP`, `SCHEMA_REG_URL`, `OPENSEARCH_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`).

Run locally
- Start deps: `make local-up`
- Implement service, then run with your language/runtime on `PORT`.

