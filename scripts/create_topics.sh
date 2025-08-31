#!/usr/bin/env bash
set -euo pipefail

BROKER="${KAFKA_BOOTSTRAP:-localhost:9092}"
TOPICS=(
  "events.catalog.product-updated:3:1"
  "events.orders.order-created:3:1"
)

create_with_cli() {
  local topic="$1" partitions="$2" rf="$3"
  kafka-topics --bootstrap-server "$BROKER" --create --if-not-exists \
    --topic "$topic" --partitions "$partitions" --replication-factor "$rf"
}

create_with_docker() {
  local topic="$1" partitions="$2" rf="$3"
  docker exec mini_kafka kafka-topics --bootstrap-server kafka:29092 --create --if-not-exists \
    --topic "$topic" --partitions "$partitions" --replication-factor "$rf"
}

echo "Creating Kafka topics..."
for spec in "${TOPICS[@]}"; do
  IFS=':' read -r name parts rf <<< "$spec"
  if command -v kafka-topics >/dev/null 2>&1; then
    create_with_cli "$name" "$parts" "$rf" || true
  elif command -v docker >/dev/null 2>&1; then
    create_with_docker "$name" "$parts" "$rf" || true
  else
    echo "No kafka-topics or docker found; cannot create topic $name" >&2
  fi
done

echo "Topic creation complete."

