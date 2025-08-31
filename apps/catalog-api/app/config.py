import os
from pydantic import BaseModel


class Settings(BaseModel):
    service_name: str = os.getenv("SERVICE_NAME", "catalog-api")
    port: int = int(os.getenv("PORT", "8001"))

    db_url: str | None = os.getenv("DB_URL")
    redis_url: str | None = os.getenv("REDIS_URL")
    opensearch_url: str = os.getenv("OPENSEARCH_URL", "http://localhost:9200")

    enable_kafka: bool = os.getenv("ENABLE_KAFKA", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    topic_product_updated: str = os.getenv(
        "TOPIC_PRODUCT_UPDATED", "events.catalog.product-updated"
    )

    cache_ttl_seconds: int = int(os.getenv("CACHE_TTL_SECONDS", "30"))
    search_cache_ttl_seconds: int = int(os.getenv("SEARCH_CACHE_TTL_SECONDS", "15"))
    otlp_endpoint: str | None = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    validate_avro: bool = os.getenv("VALIDATE_AVRO", "false").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def get_settings() -> Settings:
    return Settings()
