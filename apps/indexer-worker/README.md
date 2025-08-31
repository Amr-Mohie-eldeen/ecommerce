# Indexer Worker

Consumes `ProductUpdated` events from Kafka and upserts documents to OpenSearch.

Environment
- `WORKER_CONCURRENCY` (default 4)
- Shared: `KAFKA_BOOTSTRAP`, `SCHEMA_REG_URL`, `OPENSEARCH_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`.

Notes
- Ensure idempotency using `updated_at` semantics and OpenSearch external versioning.

