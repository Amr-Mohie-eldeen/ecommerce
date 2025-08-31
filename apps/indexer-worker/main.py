import asyncio
import os
import time
from typing import List

SERVICE = os.getenv("SERVICE_NAME", "indexer-worker")

try:
    from aiokafka import AIOKafkaConsumer
except Exception:  # pragma: no cover
    AIOKafkaConsumer = None  # type: ignore


def kafka_enabled() -> bool:
    return os.getenv("ENABLE_KAFKA", "false").lower() in {"1", "true", "yes", "on"}


# OpenSearch client setup
_os_client = None


def get_os_client():
    global _os_client
    if _os_client is not None:
        return _os_client
    try:
        from opensearchpy import OpenSearch

        url = os.getenv("OPENSEARCH_URL", "http://localhost:9200")
        _os_client = OpenSearch(hosts=[url])
        return _os_client
    except Exception as e:
        print(f"[{SERVICE}] OpenSearch client init failed: {e}")
        return None


def ensure_index(index: str = "products"):
    client = get_os_client()
    if client is None:
        return
    try:
        if not client.indices.exists(index=index):
            body = {
                "settings": {"number_of_shards": 1, "number_of_replicas": 0},
                "mappings": {
                    "properties": {
                        "product_id": {"type": "keyword"},
                        "name": {"type": "text"},
                        "description": {"type": "text"},
                        "price": {"type": "float"},
                        "updated_at": {"type": "date", "format": "epoch_millis"},
                    }
                },
            }
            client.indices.create(index=index, body=body)
            print(f"[{SERVICE}] created index '{index}'")
    except Exception as e:
        print(f"[{SERVICE}] ensure_index error: {e}")


async def consume_loop():
    if AIOKafkaConsumer is None:
        print(f"[{SERVICE}] aiokafka not installed; falling back to heartbeat.")
        heartbeat()
        return

    bootstrap = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
    topics: List[str] = [
        os.getenv("TOPIC_PRODUCT_UPDATED", "events.catalog.product-updated"),
        os.getenv("TOPIC_ORDER_CREATED", "events.orders.order-created"),
    ]
    group_id = os.getenv("KAFKA_GROUP_ID", f"{SERVICE}")

    while True:
        try:
            consumer = AIOKafkaConsumer(
                *topics,
                bootstrap_servers=bootstrap,
                group_id=group_id,
                enable_auto_commit=True,
                auto_offset_reset="earliest",
            )
            await consumer.start()
            print(f"[{SERVICE}] consuming from topics: {topics}")
            try:
                async for msg in consumer:
                    try:
                        key = msg.key.decode() if msg.key else None
                        val = msg.value.decode()
                        print(
                            f"[{SERVICE}] received topic={msg.topic} key={key} value={val}"
                        )
                        # Attempt to upsert into OpenSearch for product updates
                        if msg.topic.endswith("product-updated"):
                            upsert_product(val)
                    except Exception as e:
                        print(f"[{SERVICE}] error decoding message: {e}")
            finally:
                await consumer.stop()
        except Exception as e:
            print(f"[{SERVICE}] Kafka consumer error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)


def upsert_product(raw: str, index: str = "products"):
    """
    Upsert product document using external_gte semantics with updated_at as version.
    Expects JSON with keys: id, name, price, description?, updated_at(epoch millis)
    """
    import json

    try:
        data = json.loads(raw)
    except Exception as e:
        print(f"[{SERVICE}] invalid JSON payload: {e}")
        return

    client = get_os_client()
    if client is None:
        return

    ensure_index(index)

    doc_id = data.get("id") or data.get("product_id")
    if not doc_id:
        print(f"[{SERVICE}] missing product id in event: {data}")
        return

    version = int(data.get("updated_at", 0))
    body = {
        "product_id": doc_id,
        "name": data.get("name"),
        "description": data.get("description"),
        "price": data.get("price"),
        "updated_at": version,
    }

    try:
        client.index(
            index=index,
            id=doc_id,
            body=body,
            params={"version": version, "version_type": "external_gte"},
        )
        print(f"[{SERVICE}] upserted product {doc_id} v{version}")
    except Exception as e:
        print(f"[{SERVICE}] OpenSearch upsert error: {e}")


def heartbeat():
    i = 0
    while True:
        i += 1
        print(f"[{SERVICE}] heartbeat {i} - consuming events (stub)")
        time.sleep(5)


def main():
    # Start Prometheus metrics HTTP server if available
    try:
        from prometheus_client import start_http_server

        metrics_port = int(os.getenv("METRICS_PORT", "9104"))
        start_http_server(metrics_port)
        print(f"[{SERVICE}] metrics server on :{metrics_port}")
    except Exception:
        pass

    if kafka_enabled():
        try:
            asyncio.run(consume_loop())
            return
        except Exception as e:
            print(f"[{SERVICE}] asyncio error: {e}; falling back to heartbeat")
    heartbeat()


if __name__ == "__main__":
    main()
