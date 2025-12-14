# Dead Letter Queue (DLQ) handling
from .kafka_producer import send_event


def send_to_dlq(producer, original_event, reason: str):
    dlq_event = {
        "meta": {
            "event_type": "dlq",
            "reason": reason,
            "source": "inventory-worker",
        },
        "data": original_event
    }
    send_event(
        producer=producer,
        topic="inventory.dlq",
        event=dlq_event,
        key=original_event["meta"]["event_id"]
    )
