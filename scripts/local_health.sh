#!/usr/bin/env bash
set -euo pipefail

ok()  { printf "[OK] %s\n"  "$1"; }
fail(){ printf "[ERR] %s\n" "$1"; }

check_tcp() {
  local host="$1" port="$2" name="$3"; shift 3 || true
  if (echo > /dev/tcp/${host}/${port}) >/dev/null 2>&1; then ok "$name (${host}:${port})"; else fail "$name (${host}:${port})"; fi
}

check_http() {
  local url="$1" name="$2"
  if command -v curl >/dev/null 2>&1; then
    if curl -fsS --max-time 2 "$url" >/dev/null; then ok "$name ($url)"; else fail "$name ($url)"; fi
  else
    # Fallback to TCP if curl unavailable
    local host port
    host=$(echo "$url" | awk -F[/:] '{print $4}')
    port=$(echo "$url" | awk -F[/:] '{print $5}')
    check_tcp "$host" "$port" "$name"
  fi
}

echo "Checking local dependencies..."
check_tcp localhost 5432 "PostgreSQL"
check_tcp localhost 6379 "Redis"
check_tcp localhost 9092 "Kafka"
check_http http://localhost:8081 "Schema Registry"
check_http http://localhost:9200 "OpenSearch"
check_http http://localhost:5601 "OpenSearch Dashboards"
check_http http://localhost:16686 "Jaeger UI"

echo "Done."

