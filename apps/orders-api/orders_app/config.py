import os
from pydantic import BaseModel


class Settings(BaseModel):
    service_name: str = os.getenv("SERVICE_NAME", "orders-api")
    port: int = int(os.getenv("PORT", "8002"))

    db_url: str | None = os.getenv("DB_URL")
    redis_url: str | None = os.getenv("REDIS_URL")

    enable_kafka: bool = os.getenv("ENABLE_KAFKA", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    topic_order_created: str = os.getenv(
        "TOPIC_ORDER_CREATED", "events.orders.order-created"
    )
    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "30"))
    otlp_endpoint: str | None = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    validate_avro: bool = os.getenv("VALIDATE_AVRO", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_settings() -> Settings:
    return Settings()
