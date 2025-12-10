import json
import uuid
from datetime import datetime
from confluent_kafka import Producer
from typing import Any, Dict 

def wrap_event(event_type: str, source: str, data: dict) -> dict:
    return {
        "meta": {
            "event_type": event_type,
            "event_version": "v1",
            "event_id": str(uuid.uuid4()),
            "source": source,
            "timestamp": datetime.utcnow().isoformat(),
        },
        "data": data
    }
    


def create_producer(bootstrap_servers: str = "localhost:19092") -> Producer:
    config = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "msa-python",
        "acks": "all",
    }
    return Producer(config)

def send_event(
    producer: Producer,
    topic: str,
    key: str,
    value: Dict[str, Any] | None = None,
    event: Dict[str, Any] | None = None,
) -> None:
    """Produce a JSON-encoded message with delivery logging."""

    payload = value if value is not None else event
    if payload is None:
        raise ValueError("send_event requires `value` (preferred) or `event` data.")

    def delivery_report(err, msg):
        if err is not None:
            print(f"Delivery failed: {err}")
        else:
            print(
                f"Delivered to {msg.topic()} [{msg.partition()}] "
                f"offset={msg.offset()}"
            )

    producer.produce(
        topic=topic,
        key=key.encode("utf-8"),
        value=json.dumps(payload).encode("utf-8"),
        callback=delivery_report,
    )

    # 비동기 이벤트 처리
    producer.poll(0)
