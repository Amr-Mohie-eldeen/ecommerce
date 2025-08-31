# Recommender Service

Route (v1):
- GET `/recommendations?customer_id=...`

Environment
- `PORT` (default 8003)
- Shared: `REDIS_URL`, `OPENSEARCH_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`.

