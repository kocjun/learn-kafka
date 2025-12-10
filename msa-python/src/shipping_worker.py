import json
from datetime import datetime
from typing import Any, Dict

from confluent_kafka import Message
from .kafka_producer import create_producer, send_event, wrap_event
from .kafka_consumer import create_consumer, run_consumer_loop

producer = create_producer()

order_states: dict[str, Dict[str, Any]] = {}

def update_state_from_inventory(event: Dict[str, Any]) -> None:
    order_id = event["order_id"]
    state = order_states.setdefault(order_id, {})
    state["inventory_status"] = event["status"]
    state["inventory_event"] = event
    
def update_state_from_payment(event: Dict[str, Any]) -> None:
    order_id = event["order_id"]
    state = order_states.setdefault(order_id, {})
    state["payment_status"] = event.get("status", "approved")
    state["payment_event"] = event
    
def try_create_shipping(order_id: str) -> None:
    state = order_states.get(order_id)
    if not state:
        return
    
    if state.get("inventory_status") == "reserved" and state.get("payment_status") == "approved":
        # 배송 이벤트 생성
        inventory_event = state["inventory_event"]
        payment_event = state["payment_event"]
        
        shipping_event = {
            "order_id": order_id,
            "user_id": payment_event["user_id"],
            "product_id": inventory_event["product_id"],
            "quantity": inventory_event["quantity"],
            "amount": payment_event["amount"],
            "created_at": datetime.utcnow().isoformat(),
            "source": "shipping-worker",
            "version": "v1",
        }
        shipping_envelope = wrap_event(
            event_type="shipping.created",
            source="shipping-worker",
            data=shipping_event,
        )
        
        send_event(
            producer = producer,
            topic = "shipping",
            key = order_id,
            value = shipping_envelope,
        )
        
        log_event = {
            "order_id": order_id,
            "created_at": datetime.utcnow().isoformat(),
            "source": "shipping-worker",
            "version": "v1",
        }
        log_envelope = wrap_event(
            event_type="log.shipping.created",
            source="shipping-worker",
            data=log_event,
        )

        send_event(
            producer = producer,
            topic = "logs",
            key = order_id,
            value = log_envelope,
        )
        
        del order_states[order_id]
        
def handle_message(msg: Message) -> None:
    value = msg.value()
    if value is None:
        return
    
    envelope = json.loads(value.decode("utf-8"))
    meta = envelope.get("meta", {})
    event = envelope.get("data", {})
    event_type = meta.get("event_type")
    order_id = event.get("order_id")
    topic = msg.topic()

    inventory_events = {"inventory.reserved", "inventory.failed"}

    if topic == "inventory" and event_type in inventory_events:
        update_state_from_inventory(event)
    elif topic == "payments" and event_type == "payment.approved":
        update_state_from_payment(event)
    else:
        print(f"Skipping event type {event_type} from topic {topic}")
        return

    if order_id:
        try_create_shipping(order_id)
        
def main() -> None:
    consumer = create_consumer(
        group_id = "shipping-worker",
        topics = ["inventory", "payments"],
    )
    run_consumer_loop(consumer, handle_message)

if __name__ == "__main__":
    main()

    
