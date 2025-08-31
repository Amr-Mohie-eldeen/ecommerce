#!/usr/bin/env bash
set -euo pipefail

ok()  { printf "[OK] %s\n"  "$1"; }
fail(){ printf "[ERR] %s\n" "$1"; }

check_http() {
  local url="$1" name="$2"
  if curl -fsS --max-time 3 "$url" >/dev/null; then ok "$name ($url)"; else fail "$name ($url)"; fi
}

echo "Checking app endpoints..."
check_http http://localhost:8001/healthz "catalog-api"
check_http http://localhost:8002/healthz "orders-api"
check_http http://localhost:8003/healthz "recommender-svc"
echo "Done."

