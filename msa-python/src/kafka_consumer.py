from confluent_kafka import Consumer, KafkaException, Message

from typing import Callable, List
import signal
import time
import os

BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")

def create_consumer(
    group_id: str,
    topics: List[str],
    bootstrap_servers: str | None = None,
) -> Consumer:
    bootstrap = bootstrap_servers or BOOTSTRAP
    config = {
        "bootstrap.servers": bootstrap,
        "group.id": group_id,
        "auto.offset.reset": "earliest", # 처음부터 읽기 (개발용)
        "enable.auto.commit": False,   # 수동 커밋
        "max.poll.interval.ms": 300000, # 5분
    }
    consumer = Consumer(config)
    consumer.subscribe(topics)
    return consumer


def run_consumer_loop(
    consumer: Consumer,
    handle_message: Callable[[Message], None],
    poll_timeout: float = 1.0,
) -> None:
    running = True
    
    def stop(sig, frame):
        nonlocal running
        print("Stopping consumer...")
        running = False

    # Register graceful shutdown handlers
    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    
    try:
        print("Starting consumer loop... Press Ctrl+C to stop.")
        while running:
            msg = consumer.poll(poll_timeout)
            if msg is None:
                continue

            if msg.error():
                raise KafkaException(msg.error())

            sucess = handle_message(msg)
            
            # 성공시에만 커밋
            if sucess:
                consumer.commit(msg)
    except KafkaException as exc:
        print(f"Kafka error: {exc}")
    finally:
        consumer.close()
        print("Consumer closed.")
            
              
    
