# Contracts

Schema and event conventions for the platform.

- Subjects: `<EventName>-value` (e.g., `ProductUpdated-value`).
- Namespacing: Avro `namespace` reflects domain (e.g., `events.catalog`).
- Compatibility: prefer backward-compatible changes (add optional fields with defaults).
- Location: Avro schemas in `contracts/avro/*.avsc`.
- Reviews: PRs that change events must include Schema Registry subject, version notes, and impacted services.

Local workflow
- Start deps: `make local-up`
- Register schemas: `make seed-data` (best-effort registration)
- Create topics: `make create-topics`

Default topics
- `events.catalog.product-updated`
- `events.orders.order-created`

