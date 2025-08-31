# Mini-Commerce Platform PRD

## Overview

A microservices-based e-commerce platform demonstrating modern cloud-native patterns with event-driven architecture, observability, and recommendation systems.

## 🚀 Quick Start (Local Development)

**Priority: Get local environment running first with Docker Compose**

### Prerequisites
- Docker & Docker Compose
- Make
- Git

### Local Setup Commands
```bash
make local-up     # Start all services with Docker Compose
make seed-data    # Load sample products
make test-local   # Run integration tests
make local-down   # Stop all services
```

## Phase 1: Local Development Foundation 🐳

**Focus: Docker Compose setup for rapid development**

### T1.1 Docker Compose Infrastructure
**Priority: HIGH - Start here**
- **Services**: PostgreSQL, Redis, Kafka + Zookeeper, OpenSearch, Jaeger, Prometheus, Grafana
- **Acceptance Criteria**: `docker-compose up` brings up all dependencies
- **Output**: `docker-compose.yml`, `local/` config files
- **Time Estimate**: 2-3 hours

### T1.2 Local Development Tools
- **Tools**: Makefile targets, seed data scripts, health checks
- **Acceptance Criteria**: `make local-health` shows all services green
- **Output**: `Makefile`, `scripts/seed_local.sh`, `search/products.json`
- **Time Estimate**: 1-2 hours

## Phase 2: Core Services Development 🔧

**Focus: Build services that work locally first**

### T2.1 Common Library
- **Components**: Config, logging, telemetry, Kafka adapters, DB helpers
- **Acceptance Criteria**: Unit tests pass, reusable across services
- **Output**: `apps/common/`
- **Time Estimate**: 3-4 hours

### T2.2 Catalog API v1
**Priority: HIGH - Core service**
- **Routes**: `POST /products`, `GET /products/{id}`, `GET /search`
- **Features**: Redis caching, OpenTelemetry, Prometheus metrics
- **Events**: Emits `ProductUpdated` to Kafka
- **Acceptance Criteria**: Unit tests + local e2e tests pass
- **Output**: `apps/catalog-api/`
- **Time Estimate**: 4-6 hours

### T2.3 Indexer Worker v1
**Priority: HIGH - Enables search**
- **Function**: Consume `ProductUpdated`, upsert to OpenSearch
- **Features**: Idempotency with `external_gte`, DLQ on failure
- **Acceptance Criteria**: Integration test proves idempotency
- **Output**: `apps/indexer-worker/`
- **Time Estimate**: 3-4 hours

### T2.4 Orders API v1
- **Routes**: `POST /orders`, `GET /orders/{id}`
- **Events**: Emits `OrderCreated` to Kafka
- **Acceptance Criteria**: Unit tests + local e2e tests pass
- **Output**: `apps/orders-api/`
- **Time Estimate**: 3-4 hours

## Phase 3: Cloud Infrastructure ☁️

**Note: Only after local development is solid**

### T3.1 Terraform Backend
- **Components**: S3 bucket, DynamoDB lock table
- **Acceptance Criteria**: `terraform init` with remote backend works
- **Output**: `infra/00-backend/`

### T3.2 VPC and EKS
- **Components**: VPC, subnets, NAT, EKS cluster, managed node group
- **Acceptance Criteria**: `kubectl get nodes` works
- **Output**: `infra/10-network/`, `infra/20-eks/`

### T3.3 IAM and ECR
- **Components**: OIDC role for GitHub Actions, ECR repositories
- **Acceptance Criteria**: Role assumption and ECR push work
- **Output**: `infra/30-iam/`, `infra/50-ecr/`

### T3.4 Managed Services
- **MSK**: Serverless Kafka for events
- **RDS**: PostgreSQL for transactional data
- **ElastiCache**: Redis for caching
- **OpenSearch**: Search and analytics
- **Acceptance Criteria**: Connectivity from EKS pods
- **Output**: `infra/40-messaging-msk/`, `infra/60-data/`

## Phase 4: Platform Add-ons 📊

### T4.1 Observability Stack
- **Components**: Prometheus, Grafana, Jaeger, Loki
- **Acceptance Criteria**: Dashboards accessible, metrics flowing
- **Output**: `infra/70-addons/`

## Observability (Local)

- Tracing: Jaeger via OTEL exporter (local dev)
- Metrics: Prometheus scrapes per-service `/metrics` endpoints
  - catalog-api: `:8001/metrics`
  - orders-api: `:8002/metrics`
  - recommender-svc: `:8003/metrics`
  - indexer-worker: Prometheus client HTTP server on `:9104`
- Dashboards: Grafana (local dev) with Prometheus as datasource
- Logs: stdout in containers, optional OpenSearch Dashboards for viewing

Compose includes: PostgreSQL, Redis, Kafka + Zookeeper, Schema Registry, OpenSearch, Jaeger, Prometheus, Grafana.

Golden signals to monitor:
- Request rate, latency, error rate for APIs
- Worker processing rate and lag (future additions)

### T4.2 Ingress and Security
- **Components**: NGINX Ingress, External Secrets Operator
- **Acceptance Criteria**: Public endpoints work, secrets projected
- **Output**: Helm releases

## Phase 5: Kubernetes Deployment 🚢

### T5.1 Helm Charts
- **Components**: Deployment, Service, HPA, PDB, NetworkPolicy per app
- **Acceptance Criteria**: `helm lint` passes, pods healthy
- **Output**: `k8s/charts/`, `k8s/values/dev.yaml`

### T5.2 CI/CD Pipeline
- **Components**: GitHub Actions for build, test, deploy
- **Acceptance Criteria**: Merge to main deploys to dev
- **Output**: `.github/workflows/ci-cd.yaml`

## Phase 6: Recommendations 🎯

### T6.1 Recommendation Service
- **Route**: `GET /recommendations?customer_id=...`
- **Logic**: Popularity-based using OpenSearch/Redis
- **Acceptance Criteria**: Unit tests pass, traces visible
- **Output**: `apps/recommender-svc/`

### T6.2 Enhanced Events
- **Events**: Add `ProductViewed` for recommendation signals
- **Acceptance Criteria**: Events visible in local and dev environments
- **Output**: Enhanced event producers

## 🏃‍♂️ 8-Hour Sprint Priority

**Recommended order for maximum value:**

1. **Hours 1-3**: Phase 1 (T1.1, T1.2) - Docker Compose setup
2. **Hours 4-6**: Phase 2 (T2.1, T2.2) - Common lib + Catalog API
3. **Hours 7-8**: Phase 2 (T2.3) - Indexer worker for search

**If time allows**: Add T2.4 (Orders API) and T6.1 (Recommendations stub)

## Configuration Matrix

| Variable | Local (Docker Compose) | Cloud (AWS) |
|----------|------------------------|-------------|
| `DB_URL` | `postgresql+asyncpg://app:postgres@localhost:5432/appdb` | From SSM, RDS endpoint |
| `REDIS_URL` | `redis://localhost:6379/0` | From SSM, ElastiCache endpoint |
| `KAFKA_BOOTSTRAP` | `localhost:9092` | MSK bootstrap DNS |
| `SCHEMA_REG_URL` | `http://localhost:8081` | Glue registry endpoint |
| `OPENSEARCH_URL` | `http://localhost:9200` | OpenSearch Service endpoint |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://localhost:4317` | Collector sidecar |

## Acceptance Scenarios

### Scenario A: Product Lifecycle
```
GIVEN Docker Compose is running
WHEN I POST /products with product data
THEN ProductUpdated event is published to Kafka
AND indexer processes the event and updates OpenSearch
AND GET /search returns the product within 2 seconds
AND subsequent searches hit Redis cache
```

### Scenario B: Order Processing
```
GIVEN a product exists in the catalog
WHEN I POST /orders with that product
THEN OrderCreated event is published
AND indexer increments product popularity
AND GET /recommendations includes that product
```

### Scenario C: Local Development Parity
```
GIVEN all services running via Docker Compose
WHEN I run the test suite
THEN all tests pass without external cloud dependencies
```

## Engineering Practices

### Architecture Patterns
- **Ports and Adapters**: Thin HTTP controllers, interfaces for all I/O
- **Event Sourcing**: Kafka events for state changes
- **CQRS**: Separate read/write models with OpenSearch for queries

### Reliability
- **Idempotency**: Use `external_gte` with `updated_at` timestamps
- **Backpressure**: Small batch sizes, exponential backoff
- **Circuit Breakers**: Fail fast on downstream errors

### Observability
- **Tracing**: OpenTelemetry spans for all operations
- **Metrics**: Prometheus metrics for SLIs
- **Logging**: Structured logs with correlation IDs

### Configuration
- **Local**: `.env` files and Docker Compose
- **Cloud**: AWS SSM Parameter Store / Secrets Manager
- **12-Factor**: Environment-based configuration

## Project Structure

```
mini-commerce/
├── apps/                          # Microservices
│   ├── common/                    # Shared libraries
│   ├── catalog-api/              # Product management
│   ├── orders-api/               # Order processing
│   ├── indexer-worker/           # Search indexing
│   └── recommender-svc/          # Recommendations
├── contracts/avro/               # Event schemas
├── k8s/                          # Kubernetes manifests
│   ├── charts/                   # Helm charts
│   └── values/                   # Environment configs
├── infra/                        # Terraform modules
│   ├── 00-backend/              # State management
│   ├── 10-network/              # VPC, subnets
│   ├── 20-eks/                  # Kubernetes cluster
│   ├── 30-iam/                  # Roles and policies
│   ├── 40-messaging-msk/        # Kafka cluster
│   ├── 50-ecr/                  # Container registry
│   ├── 60-data/                 # RDS, Redis, OpenSearch
│   └── 70-addons/               # Observability stack
├── local/                        # Local development
│   ├── docker-compose.yml       # All services
│   └── configs/                 # Service configurations
├── scripts/                      # Automation scripts
├── .github/workflows/           # CI/CD pipelines
└── docs/                        # Documentation
```

## Event Schemas

### ProductUpdated Event
```json
{
  "type": "record",
  "name": "ProductUpdated",
  "namespace": "events.catalog",
  "fields": [
    {"name": "event_id", "type": "string"},
    {"name": "occurred_at", "type": "string"},
    {"name": "product_id", "type": "string"},
    {"name": "name", "type": "string"},
    {"name": "description", "type": "string"},
    {"name": "price", "type": "double"},
    {"name": "stock_qty", "type": "int"},
    {"name": "updated_at", "type": "string"}
  ]
}
```

### OpenSearch Index Mapping
```json
{
  "settings": {
    "number_of_shards": 1,
    "number_of_replicas": 0
  },
  "mappings": {
    "properties": {
      "product_id": {"type": "keyword"},
      "name": {"type": "text"},
      "description": {"type": "text"},
      "price": {"type": "double"},
      "stock_qty": {"type": "integer"},
      "popularity": {"type": "double"},
      "updated_at": {"type": "date"},
      "embedding": {
        "type": "knn_vector",
        "dimension": 384,
        "method": {
          "engine": "nmslib",
          "space_type": "cosinesimil"
        }
      }
    }
  }
}
```

## Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Docker Compose complexity | High | Start simple, add services incrementally |
| Local/cloud config drift | Medium | Shared configuration templates |
| Service startup dependencies | Medium | Health checks and retry logic |
| Test data management | Low | Automated seed scripts |

## Future Roadmap

### Phase 7: Advanced Features
- Vector embeddings for semantic search
- Real-time ML feature store (Feast)
- Advanced recommendation algorithms

### Phase 8: Production Hardening
- ArgoCD for GitOps
- Canary deployments
- Advanced monitoring and alerting
- Performance testing with k6

### Phase 9: Data Platform
- MSK Connect for S3 data lake
- Athena for analytics
- Real-time feature engineering
