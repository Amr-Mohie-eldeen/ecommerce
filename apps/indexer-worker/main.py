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
                    except Exception as e:
                        print(f"[{SERVICE}] error decoding message: {e}")
            finally:
                await consumer.stop()
        except Exception as e:
            print(f"[{SERVICE}] Kafka consumer error: {e}. Retrying in 5s...")
            await asyncio.sleep(5)


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
