import json
from datetime import datetime
from typing import Any, Dict

from confluent_kafka import Message

from .kafka_consumer import create_consumer, run_consumer_loop
from .kafka_producer import create_producer, send_event, wrap_event

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
    value = msg.value()
    if value is None:
        return
    
    envelope = json.loads(value.decode("utf-8"))
    meta = envelope.get("meta", {})
    event = envelope.get("data", {})
    print(f"Received event: {meta.get('event_type')} data={event}")
    
    inv_event = simulate_inventory_check(event)
    
    # 1) inventory 토픽으로 결과 이벤트 발행
    emit_inventory_event(inv_event)

    # 2) logs 토픽으로 로그 이벤트 발행
    emit_log_event(event, inv_event)


def main() -> None:
    consumer = create_consumer(
        group_id = "inventory-worker",
        topics = ["orders"],
    )
    run_consumer_loop(consumer, handle_order_message)


if __name__ == "__main__":
    main()
        
        
