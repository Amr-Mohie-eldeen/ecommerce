# Repository Guidelines

## Project Structure & Modules
- `apps/`: Microservices — `common/`, `catalog-api/`, `orders-api/`, `indexer-worker/`, `recommender-svc/`.
- `contracts/avro/`: Event schemas (e.g., `ProductUpdated`).
- `local/`: Local dev — `docker-compose.yml`, `configs/`.
- `infra/`: Terraform — `00-backend/`, `10-network/`, `20-eks/`, `30-iam/`, `40-messaging-msk/`, `50-ecr/`, `60-data/`, `70-addons/`.
- `k8s/`: Helm charts and env values.
- `scripts/`: Automation (seeding, health checks).
- `.github/workflows/`: CI/CD pipelines.
- `PRD.md`: Canonical product and architecture spec — build against this.

## Build, Test, and Development
- `make local-up`: Start all services with Docker Compose.
- `make local-health`: Print health of local dependencies.
- `make seed-data`: Load sample products for search/tests.
- `make test-local`: Run unit/integration tests against Compose.
- `make local-down`: Stop and clean up.
- Example: `docker compose -f local/docker-compose.yml up -d` if Make is unavailable.

## Coding Style & Naming
- Directories/services: kebab-case (e.g., `catalog-api`, `indexer-worker`).
- Modules/packages: follow language defaults (Python: snake_case; TypeScript: kebab-case; Go: lowerCamel for identifiers).
- Architecture: Ports-and-Adapters; no I/O in domain code; emit events for state changes.
- Formatters/linters: use per-language standard (Python: Black+Ruff; TypeScript: ESLint+Prettier; Go: `gofmt`+`golangci-lint`).

## Testing Guidelines
- Place tests under `apps/*/tests` or alongside code.
- Naming: `test_*.py`, `*.spec.ts`, `*_test.go`.
- Unit tests mock I/O; integration relies on Compose (Kafka, Redis, OpenSearch, Postgres).
- Run `make test-local`; add acceptance checks mirroring scenarios in `PRD.md`.

## Commit & Pull Requests
- Use Conventional Commits (e.g., `feat(catalog-api): add GET /products/{id}`).
- Scope = service or area (`indexer-worker`, `infra`, `k8s`).
- PRs: include description, linked issue, local run steps, and screenshots/logs if behavior changes. Update schemas (`contracts/avro`) and docs when events/APIs change.
- CI must be green before merge.

## Security & Configuration
- Never commit secrets. Local via `.env`/Compose; cloud via AWS SSM/Secrets Manager.
- Core env vars: `DB_URL`, `REDIS_URL`, `KAFKA_BOOTSTRAP`, `SCHEMA_REG_URL`, `OPENSEARCH_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`.
- For Kubernetes, manage secrets via External Secrets; avoid plaintext values in Git.

