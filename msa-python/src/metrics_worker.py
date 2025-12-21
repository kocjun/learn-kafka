import json
from datetime import datetime
from typing import Any, Dict

from confluent_kafka import Message

from .kafka_consumer import create_consumer, run_consumer_loop
from .kafka_producer import create_producer, send_event
from .state_store import product_order_count, orders_per_minute, minute_bucket

producer = create_producer()


def _extract_timestamp(meta: Dict[str, Any], data: Dict[str, Any]) -> str:
    # meta 우선, 없으면 data.created_at, 그래도 없으면 now
    ts = meta.get("timestamp") or data.get("created_at")
    if not ts:
        ts = datetime.utcnow().isoformat()
    return ts


def handle_order_event(msg: Message):
    try:
        event = json.loads(msg.value().decode("utf-8"))
        meta = event.get("meta", {})
        data = event.get("data", {})
    except Exception as exc:  # noqa: BLE001
        print(f"metrics-worker: failed to decode message: {exc}")
        return False

    event_type = meta.get("event_type")
    if event_type != "order.created":
        return True

    product_id = data.get("product_id")
    if not product_id:
        print("metrics-worker: missing product_id, skipping")
        return True

    ts = _extract_timestamp(meta, data)

    # 상품별 주문 카운트 누적
    product_order_count[product_id] += 1
    product_metric_event = {
        "meta": {
            "event_type": "metric.product.order_count",
            "source": "metrics-worker",
            "timestamp": ts,
            "version": "v1",
        },
        "data": {
            "product_id": product_id,
            "order_count": product_order_count[product_id],
        },
    }

    # 분 단위 주문 카운트 누적
    bucket = minute_bucket(ts)
    orders_per_minute[bucket] += 1
    minute_metric_event = {
        "meta": {
            "event_type": "metric.orders.per_minute",
            "source": "metrics-worker",
            "timestamp": ts,
            "version": "v1",
        },
        "data": {
            "bucket": bucket,
            "count": orders_per_minute[bucket],
        },
    }

    send_event(producer, topic="metric.product.order_count", event=product_metric_event, key=product_id)
    send_event(producer, topic="metric.orders.per_minute", event=minute_metric_event, key=bucket)

    print(f"metrics updated for product={product_id}, bucket={bucket}")
    return True

def main():
    consumer = create_consumer(group_id="metrics-worker", topics=["orders"])
    run_consumer_loop(consumer, handle_order_event)


if __name__ == "__main__":
    main()
