#!/usr/bin/env bash
set -euo pipefail

log() { printf "[e2e] %s\n" "$*"; }
retry() { # retry <times> <sleep> <cmd...>
  local -i tries=$1; shift; local -i pause=$1; shift
  local i=0
  until "$@"; do i=$((i+1)); if (( i>=tries )); then return 1; fi; sleep "$pause"; done
}

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

log "Bringing up local stack (build + up)..."
make local-up >/dev/null

log "Waiting for core dependencies to be healthy..."
retry 90 2 bash -c 'bash scripts/local_health.sh | (! grep -q "\[ERR\]")' || {
  bash scripts/local_health.sh || true
  echo "Dependencies not healthy" >&2
  exit 1
}

log "Creating Kafka topics..."
retry 30 2 make create-topics >/dev/null || true

log "Checking app endpoints..."
retry 30 2 bash -c 'bash scripts/check_apps.sh | (! grep -q "\[ERR\]")'

CAT_URL=${CAT_URL:-http://localhost:8001}
ORD_URL=${ORD_URL:-http://localhost:8002}

log "Creating a product in Catalog API..."
PID=$(curl -fsS -X POST "$CAT_URL/products" \
  -H 'content-type: application/json' \
  -d '{"name":"Widget-X","price":12.34,"description":"E2E test"}' | jq -r .id)
if [[ -z "$PID" || "$PID" == "null" ]]; then echo "Failed to create product" >&2; exit 1; fi
log "Created product id=$PID"

log "Waiting for Indexer to upsert into OpenSearch..."
retry 30 2 bash -c "curl -fsS '$CAT_URL/search?q=Widget' | jq -e '.results | length > 0' >/dev/null"
SEARCH=$(curl -fsS "$CAT_URL/search?q=Widget" | jq -r '.results[0].name')
log "Search returned: $SEARCH"

log "Creating an order in Orders API..."
ORDER_PAYLOAD='{"customer_id":"c-1","currency":"USD","items":[{"product_id":"p-1","quantity":2,"unit_price":5.0},{"product_id":"p-2","quantity":1,"unit_price":10.0}]}'
OID=$(curl -fsS -X POST "$ORD_URL/orders" -H 'content-type: application/json' -d "$ORDER_PAYLOAD" | jq -r .id)
if [[ -z "$OID" || "$OID" == "null" ]]; then echo "Failed to create order" >&2; exit 1; fi
log "Created order id=$OID"

log "Fetching order..."
curl -fsS "$ORD_URL/orders/$OID" | jq -e '.total_amount == 20.0' >/dev/null
log "Order verified with expected total."

log "E2E SUCCESS"
