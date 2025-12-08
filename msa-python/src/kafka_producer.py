import json
from typing import Any, Dict 

from confluent_kafka import Producer

def create_producer(bootstrap_servers: str = "localhost:19092") -> Producer:
    config = {
        "bootstrap.servers": bootstrap_servers,
        "client.id": "order-api",
        "linger.ms": 10,
        "acks": "all",
    }
    return Producer(config)

def send_event(
    producer: Producer,
    topic: str,
    key: str, 
    value: Dict[str, Any], 
) -> None: 
    """
    공통 이벤트 발행 함수
    - value 는 dict 로 받고 JSON 으로 변환하여 전송
    """
    def delivery_report(err, msg):
        if err is not None:
            print(f"Delivery failed for record {msg.key()}: {err}")
        else:
            print(f"Record produced to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}")
    
    producer.produce(
        topic = topic,
        key = key.encode("utf-8"),
        value = json.dumps(value).encode("utf-8"),
        callback = delivery_report,
    )
    producer.poll(0) # 비동기 콜백 처리
