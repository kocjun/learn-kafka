import json
from datetime import datetime
from typing import Any, Dict

from confluent_kafka import Message

from .kafka_consumer import create_consumer, run_consumer_loop
from .kafka_producer import create_producer, send_event, wrap_event
from .idempotency import is_duplicate, mark_processed, retry_with_backoff
from .dlq import send_to_dlq

producer = create_producer()

def simulate_inventory_check(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    아주 단순한 재고 체크 로직 (데모용)
    - quantity <= 5 이면 OK
    - 그 이상이면 부족 처리
    """
    quantity = event.get("quantity", 0)
    status = "reserved" if quantity <= 5 else "failed"
    
    return {
        "order_id": event["order_id"],
        "product_id": event["product_id"],
        "quantity": quantity,
        "status": status,
        "checked_at": datetime.utcnow().isoformat(),
        "source": "inventory-worker",
        "version": "v1",
    }
    
def emit_inventory_event(inv_event: Dict[str, Any]) -> None:
    envelope = wrap_event(
        event_type=f"inventory.{inv_event['status']}",
        source="inventory-worker",
        data=inv_event,
    )
    send_event(
        producer=producer,
        topic="inventory",
        key=inv_event["order_id"],
        value=envelope,
    )
    
def emit_log_event(original_event: Dict[str, Any], inv_event: Dict[str, Any]) -> None:
    log_event = {
        "order_id": original_event["order_id"],
        "product_id": original_event["product_id"],
        "requested_quantity": original_event["quantity"],
        "inventory_status": inv_event["status"],
        "timestamp": datetime.utcnow().isoformat(),
        "source": "inventory-worker",
        "version": "v1",
    }
    envelope = wrap_event(
        event_type="log.inventory.check",
        source="inventory-worker",
        data=log_event,
    )
    send_event(
        producer=producer,
        topic="logs",
        key=log_event["order_id"],
        value=envelope,
    )
    
def handle_order_message(msg: Message) -> None:
    event = json.loads(msg.value().decode())
    meta = event["meta"]
    data = event["data"]

    event_id = meta["event_id"]
    
    # 1) 중복 체크
    if is_duplicate(event_id):
        print(f"Duplicate ignored: {event_id}")
        return True  # commit
    
    try:
        def business_logic():
            if data["quantity"] <= 5:
                status = "reserved"
            else:
                raise ValueError("out_of_stock")

            inv_event = wrap_event(
                event_type="inventory.reserved",
                source="inventory-worker",
                data={
                    "order_id": data["order_id"],
                    "product_id": data["product_id"],
                    "quantity": data["quantity"],
                    "status": status,
                }
            )
            
            send_event(
                producer=producer,
                topic="inventory",
                key=data["order_id"],
                value=inv_event,
            )

        retry_with_backoff(business_logic)
        mark_processed(event_id)
        return True

    except ValueError as e:
        # ❌ 논리 오류 → 실패 이벤트 발행 + DLQ
        fail_event = wrap_event(
            event_type="inventory.failed",
            source="inventory-worker",
            data={
                "order_id": data["order_id"],
                "product_id": data["product_id"],
                "quantity": data["quantity"],
                "status": "failed",
                "reason": str(e),
            },
        )
        send_event(
            producer=producer,
            topic="inventory",
            key=data["order_id"],
            value=fail_event,
        )
        send_to_dlq(producer, event, str(e))
        mark_processed(event_id)
        return True

    except Exception as e:
        # ❌ 재시도 실패 → 커밋하지 않음 (다시 소비)
        print(f"🔥 processing failed: {e}")
        return False


def main() -> None:
    consumer = create_consumer(
        group_id = "inventory-worker",
        topics = ["orders"],
    )
    run_consumer_loop(consumer, handle_order_message)


if __name__ == "__main__":
    main()
        
        
