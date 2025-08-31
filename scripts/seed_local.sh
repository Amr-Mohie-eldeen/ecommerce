#!/usr/bin/env bash
set -euo pipefail

DATA_FILE="search/products.json"
OS_URL="http://localhost:9200"
INDEX="products"
SCHEMA_REG_URL="${SCHEMA_REG_URL:-http://localhost:8081}"
PRODUCT_UPDATED_SCHEMA="contracts/avro/ProductUpdated.avsc"
PRODUCT_UPDATED_SUBJECT="${SCHEMA_SUBJECT_PRODUCT_UPDATED:-ProductUpdated-value}"
ORDER_CREATED_SCHEMA="contracts/avro/OrderCreated.avsc"
ORDER_CREATED_SUBJECT="${SCHEMA_SUBJECT_ORDER_CREATED:-OrderCreated-value}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required to seed data" >&2
  exit 1
fi

echo "Creating OpenSearch index: ${INDEX} (if not exists)"
curl -fsS -X PUT "${OS_URL}/${INDEX}" \
  -H 'Content-Type: application/json' \
  -d '{"settings":{"number_of_shards":1,"number_of_replicas":0}}' >/dev/null || true

if [[ -f "$DATA_FILE" ]]; then
  echo "Seeding products from ${DATA_FILE}"
  # Expecting one JSON object per line (NDJSON bulk format). If file is an array, adjust as needed.
  curl -fsS -X POST "${OS_URL}/${INDEX}/_bulk" \
    -H 'Content-Type: application/x-ndjson' \
    --data-binary @"${DATA_FILE}" >/dev/null || true
else
  echo "No ${DATA_FILE} found; seeding a sample product"
  curl -fsS -X POST "${OS_URL}/${INDEX}/_doc" \
    -H 'Content-Type: application/json' \
    -d '{"product_id":"demo-1","name":"Demo Product","description":"Seeded locally","price":9.99,"stock_qty":100,"updated_at":"2024-01-01T00:00:00Z"}' >/dev/null || true
fi

echo "Seed complete."

# Register Avro schemas with Schema Registry (best-effort)
echo "Registering Avro schemas with Schema Registry at ${SCHEMA_REG_URL} (best-effort)"

register_schema() {
  local subject="$1" file="$2"
  if [[ ! -f "$file" ]]; then
    echo "Schema file not found: $file — skipping"
    return 0
  fi

  if command -v jq >/dev/null 2>&1; then
    SCHEMA_STR=$(jq -Rs . < "$file")
  elif command -v python3 >/dev/null 2>&1; then
    SCHEMA_STR=$(python3 - <<'PY'
import json, sys
print(json.dumps(sys.stdin.read()))
PY
    < "$file")
  else
    echo "Neither jq nor python3 available to encode schema JSON — skipping $subject"
    return 0
  fi

  curl -fsS -X POST "${SCHEMA_REG_URL}/subjects/${subject}/versions" \
    -H 'Content-Type: application/vnd.schemaregistry.v1+json' \
    -d "{\"schema\": ${SCHEMA_STR}}" >/dev/null && \
    echo "Registered schema for subject ${subject}" || \
    echo "Could not register schema for subject ${subject} (Schema Registry offline?)"
}

register_schema "${PRODUCT_UPDATED_SUBJECT}" "${PRODUCT_UPDATED_SCHEMA}"
register_schema "${ORDER_CREATED_SUBJECT}" "${ORDER_CREATED_SCHEMA}"

echo "Schema registration step complete."
