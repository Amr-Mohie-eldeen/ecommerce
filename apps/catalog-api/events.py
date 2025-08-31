import json
import sys
from typing import Any, Dict


def publish_product_updated(event: Dict[str, Any]) -> None:
    """
    Stub event publisher. In Phase 3, replace with Kafka producer
    using KAFKA_BOOTSTRAP and SCHEMA_REG_URL from environment and
    contracts/avro schemas.
    """
    print(f"[events] ProductUpdated: {json.dumps(event)}", file=sys.stdout)
